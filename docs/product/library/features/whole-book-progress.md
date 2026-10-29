# 整本任务进度条（L3 实现说明）

> 建立：2026-10-29（R246；R248 补齐挂载位置，R249 补齐朗读 worker 会话隔离）。读者是**要改书籍详情页整本任务进度条的人**——这里只讲实现与边界；
> 用户视角见 L1 [`product/readme/library.md`](../../readme/library.md)；
> 本次缺陷的取舍见 LLD
> [`project/iterations/1.0/r214-book-detail/lld.md`](../../../project/iterations/1.0/r214-book-detail/lld.md) §18 / §20 / §21。

## 1. 组成

进度条位于 `cps/templates/partials/whole_book_panel.html`，由
`cps/static/js/whole-book-panel.js` 驱动。R248 起它只挂在**完整书籍详情页**
「整本任务」按钮下方的 `#whole-book-progress-slot`；书卡弹层（XHR 片段）和书架页
不渲染 slot、partial 或 JS，不会出现跨页的全局进度条。

| 区域 | 内容 | 数据来源 |
| --- | --- | --- |
| 标题 | 任务类型 + 状态，如「全文单词详解 · 进行中」 | `data-t-progress-kind-*` + `data-t-progress-*` |
| 进度条 | 百分比 | `done / total` |
| 计数 | `done / total` | 三条整本链路状态接口 |
| 继续 | 仅朗读批次失联时出现 | 状态接口 `canResume=true` |
| 关闭 | 本次页面会话收起进度条 | 前端隐藏，不取消任务 |

页面初次加载的活跃批次由 `show_book` 注入 `entry.whole_book_active`；起批成功后使用
start 接口返回的快照；之后按既有频率轮询：翻译 4 秒、朗读 5 秒、详解 30 秒。

## 2. 任务类型键必须全小写

HTML 属性名会被浏览器统一解析成小写。因此模板写
`data-t-progress-kind-worddetail`，JS 必须先执行
`String(kind).toLowerCase()`，再拼成 `progress-kind-worddetail`。

不要把按钮动作文案复用为进度标题：`start-worddetail` 的值是「打开详解页面」，
它回答“点击后做什么”，而进度标题必须回答“当前是哪条任务”。

## 3. 状态映射

| job 状态 | 标题句式 |
| --- | --- |
| `PENDING` / `RUNNING` / 其他非终态 | `{task} · 进行中` |
| `COMPLETED` | `{task} · 已完成` |
| `PARTIAL_FAILED` | `{task} · 有失败段落` |
| `CANCELED` / `CANCELLED` | `{task} · 已取消` |

状态句式与任务名都放在模板 `data-t-*` 中，JS 只做变量替换；不要在 JS 里另写中文。

## 4. 边界

- **一条进度条**：同一本书多条链路并存时按
  `translate > tts > wordDetail` 选第一条展示，其余仍在各自面板中可见。
- **只在完整详情页**：进度条随整本任务区渲染，不再移到全局导航下方；从书卡弹层
  点「整本任务」会先跳完整详情页，再在页内看到进度条。
- **关闭不等于取消**：点 `×` 只隐藏当前页面的进度条，后台任务继续；刷新后若仍有活跃批次会重新出现。
- **不改任务契约**：进度条只消费既有 start/status/retry 响应，不新建 job、不改计费、不改缓存。
- **失败可见**：轮询单次失败不清空进度；恢复按钮失败原因留在进度条内显示。
- **响应式**：窄屏允许标题、进度条、计数换行，不横向溢出。

## 5. 后台 worker 必须使用独立会话

`ub.session` 是请求线程构造并复用的普通 Session 实例，不是可以在 daemon 线程里
长期持有的线程本地会话。整本朗读的 `_synth_worker()` 因此必须经
`_thread_db_session()` 创建独立 engine + 线程作用域会话，并：

- 每段完成后通过 `_commit_with_retry(session)` 提交，不碰 `ub.session`；
- 每轮读取 job 前 `expire_all()`，让请求线程写入的 `CANCELLED` 能被及时看见；
- 统计 `done/failed` 时显式传入 worker session；
- 请求线程的 `progress()` 在提交后 `refresh(job)`，读取 worker 刚写入的终态。

若 worker 复用 `ub.session`，请求线程的 commit/close 会让 worker 下一次 autoflush
抛出 `ResourceClosedError: This transaction is closed`，批次停在 `RUNNING`，
页面只能显示「继续」。这是 R249 的生产根因。

批次台账与音频缓存是两个口径：ES/MinIO 中可能已有大部分音频（R249 实测 book 145
为 1347/1348 段），但只要本次 item 尚未逐段请求成功并标为 `DONE`，页面仍会按台账
显示进度和「继续」。不能仅凭 ES 有音频就把批次直接改成 `COMPLETED`，否则会掩盖
缺失段；续跑会命中已有缓存并快速核验，只对 miss 段真正合成。

该修复仍是 R240 迁移前的存量 daemon 临时收敛，不代表新任务可以继续复制
「每 job 一条 daemon 线程 + 进程内花名册」；整本朗读后续仍须迁入统一异步 runtime。

## 6. 测试

```bash
pytest tests/test_reading_tts_service.py tests/test_book_detail_r214.py -q
node --check cps/static/js/whole-book-panel.js
```

`test_progress_title_names_task_and_status` 钉住三类任务名、四种状态句式和小写化；
`test_whole_book_progress_slot_is_full_detail_only`、
`test_whole_book_partial_is_not_rendered_in_xhr_fragment` 与
`test_progress_bar_is_appended_to_detail_task_slot` 钉住详情页挂载边界；
改回全局 `insertAfter(navbar)`、在 XHR 片段下发 partial，或去掉 `toLowerCase()`
都必须报红。`test_synth_worker_never_uses_request_session` 把全局会话换成任何访问
都会报错的哨兵，确认 worker 只用独立会话并跑到 `COMPLETED`。
