> 归档：R194（写作批改改 SSE 进度流）原样搬移自 `response.md`。
> 2026-10-23 R216 写入触发轮转搬移，只搬移原文、不总结、不改写。（该节父级日期标题已在此前轮转中搬走，故本节以 `###` 开头原样保留。）

### R194（用户：批改要 70–150s，前端只有转圈，能否改成 SSE 显示进度）

- **背景与承接**：写作批改是同步 LLM 调用，实测 70–150s。R190 已放开无限修订、R191 已把代理预算提到 210s、moon-well R193 已让同文 revise 幂等，但用户在等待期间仍只看到按钮转圈，任何中间层 idle timeout 或部署切换都会把长连接掐断。本轮把 magicbook 侧批改主路径改为 SSE：状态行显示等待秒数，`result/error` 仍用统一信封，JSON 端点保留回退。
- **编号顺延（如实）**：本需求原占 R192，合入时发现并行部署链请求已占用本仓 R192/R193（纯文档跳过、fnOS 单链），按全史最大 +1 顺延为 **R194**；`requests.md`、L1/L2、LLD 与代码注释均已同步，分支名 `feat/r192-writing-sse` 与首条 commit 信息保留历史编号，不代表现行占号。跨仓同源 moon-well 顺延为 **R196**。
- **代理（`cps/routes/learning.py`）**：新增 `POST /ajax/learning/writing/submit/stream`、`/revise/stream`，复用 `_b1_payload` 白名单校验，`requests.post(stream=True, timeout=(10, 300))` 逐 chunk 透传；建连前 401 自动刷新 token 并重连一次，流开始后不重放；上游非 200 原样透传 body/状态码；响应加 `Cache-Control: no-cache`、`X-Accel-Buffering: no`、`Connection: keep-alive`；客户端断开时关闭上游连接，但不取消 moon-well 批改。
- **前端（`cps/static/js/learning-writing.js`）**：不用 `EventSource`（需要 POST body 与 `X-CSRFToken`），改 `fetch` + `ReadableStream` + `TextDecoder` 解析 `status/ping/result/error`；`ping.elapsedMs` 显示「Reviewing… Ns」；`result` 走既有 `renderReview` 并刷新历史；仅在 SSE 建连失败、HTTP 非 200 或尚未收到任何事件时回退一次 JSON，已收到 `status/ping` 后断网不重试。模板注入两个 stream URL。
- **契约**：`status {phase}` → `ping {elapsedMs}`（后端 5s 一条）→ `result Result<Review>` 或 `error Result`；建连前失败仍是 JSON 400/401/503。完整事件语义以 moon-well L2 为权威，本仓 L2 只维护代理映射与超时口径。
- **测试**：`tests/test_learning_writing_sse.py` 6 条（登录、submit/revise 映射、payload 白名单、响应头、401 刷新重连、上游非 200 透传）；静态守卫锁 `postSse/getReader/streamStarted` 与两个 stream URL、禁止 `new EventSource(`；i18n 种子新增 `Connection error` 并通过 po/mo 契约。定向 `test_learning_proxy.py + 上述三文件` **98 passed**；全量 `pytest -q` **630 passed / 13 failed**，13 个失败均为既有 Python 3.8 / 缺书籍 fixture 基线，无新增失败。
- **上线**：commit `2d2b2804`，merge develop **`4cded68c`**，push 后 fnOS 构建 **END OK**（17:15:45）、部署 **SUCCESS**，容器 `magicbook Up (healthy)`；回填编号与证据的 commit **`bf45c23a`** 再次 END OK（17:23:56），容器仍 healthy。线上 `learning-writing.js` 已含 `streamEndpoint/postSse`，模板已注入两个 stream URL。后端 SSE 直连复验见 moon-well R196：首条 ping 5.01s、87.61s 返回 result。
- **边界（如实）**：代理层 `X-Accel-Buffering` 与 401 重连由契约测试锁定，未用真实登录态在公网代理上做逐 chunk 计时；SSE 不降低 LLM 延迟，也不解决 blue-green 25s/40s drain 中断（已完成的批改会落库，未完成的仍需重试）；模型 token 级流式、异步 job 不在本轮。
- **台账**：分支 `feat/r192-writing-sse`，worktree `../magicbook-r192-writing-sse` 留待验收后按闸门删除；临时 merge worktree `../magicbook-r192-merge` 在文档回填推送后移除。冲突记录：与并行部署链 R192/R193 撞号，已顺延 R194；无内容冲突。
- **验收结论（2026-10-22，未通过/暂停）**：用户复测 task=2 修订稿，浏览器 Network 确认命中 `POST /ajax/learning/writing/revise/stream`、`200 OK`，约 2.5min 后 UI 报错、Response 面板为空。moon-well 同一请求 `09:29:47` 建连 37ms，`09:32:18` magpie `Read timed out` 后发出 SSE `error`；magpie 台账 `ms=150013,status=499`。结论：magicbook 的 SSE 代理与前端解析已生效，失败原因是后端 LLM 150s 预算耗尽，不是代理缓冲、也不是前端仍走旧 JSON。
- **DevTools 说明**：`text/event-stream` 的响应体在 Network → Response 为空是正常显示，应看 EventStream/事件列表；UI 报错对应后端 `error` 事件。
- **停止修复与配置回滚**：moon-well 侧曾临时把 Nacos `ai.providers.magpie.timeout-ms` 调到 240000，按用户“放弃修复”指令已回滚为 150000；本仓无新增代码改动。LLD 状态改为“已上线，真机验收未通过”。
- **总结**：requests.md 占号 R194；本仓 R192/R193 已被部署链占用，故不再重复占号。
