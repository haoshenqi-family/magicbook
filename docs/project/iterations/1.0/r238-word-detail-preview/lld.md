# R238 全文单词详解预览卡死修复 + 后台预计算 · LLD

> 状态：**已上线，待用户最终验收**（2026-10-28）
> 工作项：R238（magicbook 单仓交付）· 迭代 1.0
> 用户原话：「magicbook 全文单词详解 卡在预览加载中。booi_id=145 这是为什么？所有的书是否都会这样？能否加一个异步任务，后天提前把这个算出来」（“后天”按“后台”理解）

## 1. 结论与范围

两个问题同时存在：

1. **所有书都会卡住的确定性前端缺陷**：预览脚本早于 layout 底部 jQuery 执行，
   `$` 未定义，AJAX 请求根本没有发出。
2. **即使修好脚本，同步预览仍可能很慢**：请求线程要解析整本 EPUB，并按 2000 词
   一批串行调用 moon-well；每次 cached-check 又会触发后端索引级扫描，期间没有进度
   或持久化结果。

本轮修前端加载顺序，并把预览改为「持久化快照 + 后台线程计算 + 页面轮询」。
真正生成单词详解仍不自动执行，避免管理员只是打开预览就产生真实 token 费用。

## 2. 根因证据

- 原 `cps/templates/word_detail_batch.html` 在 `{% block body %}` 内直接写
  `<script>`，`layout.html` 的 `jquery.min.js` 在 `{% block body %}` 之后、
  `{% block js %}` 之前加载。
- 真浏览器控制台：
  `ReferenceError: $ is not defined at post (...word-detail-batch...:553:9)`，
  调用栈来自 `loadPreview()`。
- 因此 `/ajax/word-detail-preview` 一次未发出，开始按钮始终 disabled。
- 该模板对所有书共用，所以不是 `book_id=145` 专属；短书/缓存环境可能掩盖慢链路，
  但脚本错误本身与书无关。

## 3. 数据模型

新增 `cps/reading_word_detail/models.py::WordDetailPreview`：

```text
reading_word_detail_preview
  id, book_id, book_format, book_name, book_fingerprint
  status:  RUNNING | READY | FAILED
  stage:   EXTRACTING | CHECKING | READY | FAILED
  distinct_words, checked_words, cached_words, not_word_like, target_words
  missing_json, error_message, computed_at, created_at, updated_at
  UNIQUE(book_id, book_format)
```

`missing_json` 保存完整缺失词表，用于「预览刚完成就点开始」时跳过第二次 EPUB 解析
与缓存扫描；页面响应仍只暴露前 20 个样例。

建表通过 `JobServiceBase.extra_tables` 扩展公共 `_ensure_tables()`，不在子类复制
B6 已归一化的建表原语。

## 4. 后台时序

```text
POST /ajax/word-detail-preview {book_id, book_format, force?}
  ├─ 校验管理员 + 入参
  ├─ 取书目/文件，只计算 fingerprint
  ├─ 命中 READY(≤10min) / FAILED(≤60s) → 直接返回
  └─ 未命中/过期/force
       ├─ upsert RUNNING + EXTRACTING，commit
       ├─ spawn daemon worker
       └─ HTTP 立即返回 RUNNING

worker（独立 DB session）
  ├─ 二次判态，只处理 RUNNING
  ├─ extract_epub_paragraphs + distinct_words
  ├─ stage=CHECKING，按 ≤2000 词分批 check
  │    └─ 每批更新 checked_words/cached_words
  └─ READY + missing_json + computed_at
       或 FAILED + error_message
```

- 请求线程不访问 moon-well。
- 服务级锁串行化快照建行/失效/起线程；`JobServiceBase._spawn_worker()` 的花名册防
  同进程重复线程。
- worker 启动后再次检查行状态，避免轮询补线程与上一线程完成之间的竞态导致重算。
- 线程只使用请求线程定格的 moon-well token 闭包，不读取 Flask request/session。

## 5. 复用、TTL 与失败

| 状态 | 规则 |
| --- | --- |
| READY | 10 分钟内直接复用；过期后台刷新 |
| FAILED | 60 秒内复用失败；之后允许重试 |
| RUNNING | 若本进程已有 worker 则复用；进程重启后由下一次请求补线程 |
| 指纹变化 | 旧快照立即失效 |
| force=true | 绕过 READY/FAILED 窗口 |
| start() | 复用同指纹、新鲜 READY 快照的 missing_json 与计数 |

## 6. 页面修复与交互

- 脚本整体移入 `{% block js %}`，晚于 jQuery。
- RUNNING：按 `stage` 显示「正在读取正文并统计去重词…」或「正在比对详解缓存…
  已检查/总数」；每 2.5 秒轮询且仅页面可见时执行。
- READY：恢复原预览数字、缺失词样例；`targetWords > 0` 才启用开始按钮。
- FAILED：显示真实 `message`，最多做 4 次、每 15 秒一次退避轮询，不静默挂起。
- `force` 已透传到后端；当前页面正常轮询不 force，避免后台任务反复重算。

## 7. 测试与文档

- 定向回归：`tests/test_word_detail_batch_r176.py` + `tests/test_whole_book_estimate.py`
  + `tests/test_job_service_base.py`，**68 passed / 0 failed**。
- 扩展回归追加书籍详情、整本翻译/朗读共用骨架与 i18n，合计 **179 passed / 0 failed**。
- 守卫覆盖：实际渲染 jQuery 顺序、首请求不跑上游、READY/TTL/force、FAILED 退避、
  start 复用、迟到 worker 不重算、2000 词分批、公共建表原语不外叉。
- `py_compile`、`pybabel compile`、`git diff --check` 通过。
- 正式发布态全量回归：**1014 passed / 0 failed / 4 warnings**；并入
  `origin/develop` 后定向复跑 **68 passed / 0 failed**。
- 交付四问：L1 `readme/vocabulary.md`；L2 `vocabulary/interface.md`；L3
  `vocabulary/features/word-detail-preview.md`；本次实现即本 LLD。需求基线
  `vocabulary/requirements.md` 与迭代 `plan.md` 同步。

## 8. 未做与边界

- 不对全库自动批量预热，只在某本书预览页实际打开时计算。
- 不自动生成详解；预览只允许 cached-check。
- 不改 moon-well `WordDetailService.cachedLookupKeys()` 的全索引扫描。后续可另立
  跨仓任务，把查找改为按输入词表 `terms` 查询或增加短 TTL 缓存。
- **R239 备注**：上述“未改”只描述 R238 当时范围。后续 R226 已修复该扫描的
  `forms.type` 投影，预览覆盖率随之纠正；magicbook 侧仍无代码改动。
- 当前以 magicbook 单进程部署为前提使用进程内锁/花名册；多进程部署需另加 DB 租约。

## 9. 驻留与验收

- worktree：`../magicbook-r238-word-detail-preview`
- 分支：`fix/r238-word-detail-preview`
- 实现：`5bb6336e`；merge：`9577c541`；上线登记：`c0f4f598`。
- 状态：已推送 `origin/develop`，fnOS build `c0f4f5982d02de4c1e41e05ebb2da5939255db04`
  于 2026-10-28 14:33 部署成功，容器 running；worktree 原样驻留待用户最终验收。
- 生产真机（2026-10-28）：
  - `book_id=145&book_format=epub`：页面经历「正在读取正文」后自动显示 READY；
    去重 4,345、已有 1,952、待生成 2,043，按钮启用。
  - `book_id=50&book_format=epub`：去重 6,111、已有 2,269、待生成 3,411，按钮启用。
  - 两本书均实际发出 `/ajax/word-detail-preview` 并落库为 READY；控制台无
    `$ is not defined`。
  - `book_id=50` 在 10 分钟窗口内刷新后立即显示 READY，数据库 `computed_at` 保持
    `2026-10-28 06:36:00.278545`，确认命中同一快照。
  - 验收未点击「开始补缺」，未触发单词详解生成或 token 费用。
