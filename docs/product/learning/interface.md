# learning · L2 接口说明

> 读者：调用者 / 集成者。magicbook 是每日学习前端，moon-well 是 learning 后端；本文件只维护「magicbook 端点 → moon-well 端点」的映射、超时与前端消费契约。后端语义的唯一权威是 moon-well 的 `docs/product/learning/interface.md`。

## 能力边界

每日学习中枢与七个子页面（复习队列、听写、口语陪练、复述训练、计时重读、写作工坊、选书难度匹配）的代理与前端接线。词汇、阅读、TTS 等相邻模块不在本文件范围。

本文件当前先补齐 **写作批改 SSE（R194）** 子集；其余学习子功能仍以 `docs/product/readme/learning.md` 与 moon-well L2 为准，后续随演进补齐。

## 写作工坊（writing）

### 1. JSON 端点（保留，SSE 的回退路径）

| magicbook 端点 | moon-well 端点 | 超时 | 说明 |
| --- | --- | --- | --- |
| `POST /ajax/learning/writing/task/generate` | `POST /learning/writing/task/generate` | 90s | LLM 出题；请求字段白名单 `mode/cefrLevel/prompt/bookId/bookTitle/chapter` |
| `POST /ajax/learning/writing/submit` | `POST /learning/writing/submit` | 210s | 初稿批改 |
| `POST /ajax/learning/writing/revise` | `POST /learning/writing/revise` | 210s | 修订稿批改；同文重试由后端幂等复用 |
| `GET /ajax/learning/writing/task` | `GET /learning/writing/task` | 30s | 任务详情 + 各稿正文/批改（续写） |
| `GET /ajax/learning/writing/history` | `GET /learning/writing/history` | 30s | 写作历史（带 `lastDraftNo`） |

### 2. SSE 进度流（R194，主路径）

| magicbook 端点 | moon-well 端点 | 超时 | 说明 |
| --- | --- | --- | --- |
| `POST /ajax/learning/writing/submit/stream` | `POST /learning/writing/submit/stream` | 建连 10s / 单 chunk idle 300s | 初稿批改进度流 |
| `POST /ajax/learning/writing/revise/stream` | `POST /learning/writing/revise/stream` | 建连 10s / 单 chunk idle 300s | 修订稿批改进度流 |

- 请求体与 JSON 端点相同：`{"taskId":"...","text":"..."}`；代理按 `taskId`/`text` 白名单裁剪，`text` 上限 20000 字符（后端另有 4000 字符业务校验）。
- 鉴权：当前用户 session 中的 moon-well token 以 `Authorization: Bearer …` 转发，token 不下发浏览器；CSRF 与登录校验沿用 `/ajax/` 规则。建连前 401 自动刷新并重连一次；流开始后不重放。
- 响应头：`Content-Type: text/event-stream`、`Cache-Control: no-cache`、`X-Accel-Buffering: no`（禁止 Traefik/Caddy/Nginx 缓冲）。代理逐 chunk 透传，不聚合、不改写事件体。
- 事件：`status`（`{phase:"accepted"|"grading"}`）、`ping`（`{elapsedMs}`，5s 心跳）、`result`（`Result<Review>`，与 JSON 端点同形）、`error`（`Result`，`success:false` + `code` + `message`）。完整语义见 moon-well L2。
- 建连前失败：参数不合法 400、未登录 401、moon-well 未配置/不可达 503，均为 JSON；上游非 200 时原样透传 body 与状态码。
- 断线：浏览器关闭或网络中断时代理关闭上游连接；moon-well 的批改线程不取消，结果继续落库，用户刷新写作历史可取回。

### 3. 前端消费契约

- `cps/static/js/learning-writing.js` 用 `fetch` + `response.body.getReader()` 解析 SSE（不用 `EventSource`：需要 POST body 与 `X-CSRFToken`）。
- 收到 `status`/`ping` 时状态行显示「批改中… Ns」；收到 `result` 后走既有 `renderReview`，并刷新历史。
- 回退：仅当 SSE **建连失败或尚未收到任何事件**时，自动改用一次 JSON 端点；已收到 `status`/`ping` 后断网不重试，避免重复批改。后端 R196 的同文并发去重保证回退也不会重复调 LLM。
- LLM 预算：moon-well magpie 单次 150s；代理 210s 覆盖后端 + 落库余量；SSE 心跳让连接不受「整段 210s」限制。

## 调用方契约

- 统一信封：正常 200；凭证失效 401；上游业务失败 500 + `Result.code`；上游不可达由本仓自造 503 `{"success": false, "message": "… service unavailable"}`。
- 消费侧 `common/api.js`：JSON 端点走 `unwrapStrict`（非信封即抛）；SSE 的 `result`/`error` 也按同一信封解包。
- 失败文案：前端直接展示 `message`；网络层错误由浏览器 `fetch` 抛出，SSE 已开始后提示「结果可能已保存，刷新历史」。

## 相关文档

- 用户手册：[learning](../readme/learning.md)
- 后端契约：moon-well `docs/product/learning/interface.md`
- 本次实现：[writing-sse LLD](../../project/iterations/2026-10-writing-sse/writing-sse/lld.md)
