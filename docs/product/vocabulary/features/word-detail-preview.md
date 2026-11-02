# 全文单词详解预览（L3）

> 状态：现行（2026-10-28 R238，已上线待用户验收；生产已验 `book_id=145/50`）。
> 读者：修改 `word_detail_batch.html`、`reading_word_detail` 预览链路或台账建表逻辑的人。
> 需求基线：[`../requirements.md`](../requirements.md) R238；接口契约：[`../interface.md`](../interface.md) §5；
> 本次实现：[`../../../project/iterations/1.0/r238-word-detail-preview/lld.md`](../../../project/iterations/1.0/r238-word-detail-preview/lld.md)。

## 1. 根因：所有书共有的脚本加载顺序缺陷

原模板把 AJAX 初始化脚本放在 `{% block body %}` 内，而 `layout.html` 的 jQuery
在页面底部、`{% block js %}` 之前加载。浏览器执行到 `post()` 里的 `$.ajax` 时
`$` 尚未定义，立即抛 `ReferenceError`；预览请求没有发出，所以页面永远停留在
「预览加载中…」。这不是 `book_id=145` 的数据问题，而是该页面所有书共用的
前端缺陷。R238 将整段脚本移入 `{% block js %}`，并由实际渲染顺序守卫钉住。

## 2. 数据与状态

`reading_word_detail_preview` 一本书一个格式一条，唯一键 `(book_id, book_format)`。

| 字段组 | 用途 |
| --- | --- |
| `book_fingerprint` | 正文文件大小/mtime 指纹；变化时旧快照失效 |
| `status` / `stage` | `RUNNING + EXTRACTING/CHECKING`、`READY`、`FAILED` |
| `distinct_words` / `checked_words` | 后台阶段进度 |
| `cached_words` / `not_word_like` / `target_words` | 完成后预览数字 |
| `missing_json` | 完整缺失词表；只服务紧接着的 `start()` 复用，页面只取前 20 个样例 |
| `error_message` / `computed_at` / `updated_at` | 失败可见、TTL 与失败退避 |

建表仍走 `JobServiceBase._ensure_tables()` 的唯一实现；`WordDetailBatchService`
通过 `extra_tables = (WordDetailPreview,)` 声明附加表，不在子类复制建表代码。

## 3. 后台生命周期

1. `preview()` 只定位书目/文件并计算指纹，不在请求线程解析 EPUB。
2. 无快照、指纹变化、READY 超过 10 分钟或 `force=true`：重置为
   `RUNNING/EXTRACTING`，提交后用 `JobServiceBase._spawn_worker()` 起后台线程，
   请求立即返回快照。
3. 后台线程先在独立 DB session 中二次判态，只处理仍为 `RUNNING` 的行；随后解析
   正文、去重取词，进入 `CHECKING`。
4. 词表按最多 2000 词一批调用 moon-well `cached-check`；每批提交
   `checked_words/cached_words`，页面每 2.5 秒轮询可见进度。
5. 全部批次成功后写 `READY + computed_at + missing_json`；任何异常写
   `FAILED + error_message`，页面显示原因并做有限次退避重试。

同一进程用服务级锁串行化“读快照 → 重置/建行 → 起线程”，后台花名册再挡住重复
线程。RUNNING 行在进程重启后会由下一次页面请求重新补线程；这正是持久化快照而非
纯内存任务的价值。

## 4. 快照复用规则

| 条件 | 行为 |
| --- | --- |
| READY 且 `computed_at` 距今 ≤ 10 分钟 | 请求线程直接返回，不访问 moon-well |
| READY 过期 | 后台刷新；当前响应仍通常先返回 RUNNING |
| FAILED 且 `updated_at` 距今 < 60 秒 | 直接返回同一失败，避免轮询放大故障 |
| FAILED 超过 60 秒 | 允许下一次后台重试 |
| 正文指纹变化 | 无论原状态都重置重算 |
| `force=true` | 绕过 READY TTL / FAILED 退避，立即重置为 RUNNING |
| `start()` 遇 READY、指纹一致且新鲜 | 直接复用 `missing_json` 与计数，不再解析正文/扫描缓存 |

## 5. 边界与坑

- **预览只读**：只允许调用 `/vocabulary/detail/cached-check`；不得为了“提前算好”
  调用 `warm-publish-by-words` 或 `GET /vocabulary/detail/{word}`（后者 miss 会生成并计费）。
- **不在全库后台预热**：只有某本书的预览页实际被打开才创建该书任务，避免管理页
  一次访问触发全库解析与缓存扫描。
- **不是用户级快照**：缓存覆盖率是全局词库状态，快照按书保存；不包含用户私有内容。
- **线程不读 Flask request/session**：预览闭包在请求线程内定格 moon-well token，
  后台线程只持有快照，避免无请求上下文时崩溃。
- **单进程前提**：magicbook 生产入口是单 Python 进程，进程内锁与线程花名册足够；
  若未来改为多进程，需要把 RUNNING 领取升级为数据库 CAS/租约。
- **失败不静默**：解析失败、鉴权失败、上游 HTML/HTTP 故障都必须落到 `FAILED.message`
  并在页面可见，不能显示成“0 个词”或无限加载。
- **旧结果可能保守**：READY 在 10 分钟内不刷新，期间新生成的详解不会立即从缺失数
  扣除；真正入队时 moon-well 仍按 `skipCached` 跳过，因此不会重复计费。
- **上游算法更新也可能短暂滞后（R239）**：缓存命中集合由 moon-well 计算；其算法刚上线时，
  10 分钟内的 READY 快照仍可能保留旧数字。验收或算法切换后用 `force=true` 强制刷新，
  不以本仓缓存副本推断词形。magicbook 只展示上游 `cachedWords / targetWords / missingSample`。

## 6. 覆盖率消费规则（R239 复盘）

本仓是**纯消费方**，不得维护第二份词形判断。预览 worker 从正文抽取并去重字面词后，
只把词表交给 moon-well `cached-check`；后台线程和页面都不得按后缀、词干或词频秩
自行增减“已缓存”数量。

一次完整计算的数字关系：

```text
原始去重词数 = cachedWords + targetWords + notWordLike
覆盖率       = cachedWords / (cachedWords + targetWords)
targetWords  = moon-well missing.length
```

`notWordLike` 是缩略形、连字符词和无义单字母，已经被 moon-well 排除在覆盖率分母外。
因此不能写成 `原始去重词数 - cachedWords` 当目标数，也不能拿它反推 `cachedWords`；
这类算法会把噪声误算成待生成词，并在进度条上制造无法解释的差额。

排查“详情能查到、预览却说缺”时，先确认 moon-well 交互路径与索引扫描是否使用同一套
查找键和完整 `_source` 投影，再检查 READY 快照是否过期。禁止在 magicbook 侧临时加
屈折后缀表、stemming 或特判来“修数字”——那会把两仓口径永久分叉，并可能把已有详解
重复入队。

## 7. 测试锚点

`tests/test_word_detail_batch_r176.py`：

- 实际渲染页中 jQuery 早于预览脚本；模板脚本位于 `block js`。
- 首请求可立即 RUNNING 且请求线程不访问上游；READY 复用、过期刷新、force 重算。
- FAILED 60 秒退避；超过窗口后再重试；失败文案可见。
- 同一本书分批仍不超过 2000 词；预览路径不调用 publish。
- start 复用新鲜 READY 快照，不产生第二趟 cached-check。
- 迟到的补线程拿到 READY 行时直接退出，不重复计算。
- 预览计数只来自上游；本仓不维护屈折后缀或派生规则的第二份实现。

`tests/test_job_service_base.py`：`_ensure_tables()` 仍是三家唯一实现，附加表通过
`extra_tables` 扩展而非子类覆盖。
