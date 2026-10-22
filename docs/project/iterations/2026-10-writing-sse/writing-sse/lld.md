# 写作批改 SSE 进度流（magicbook R194）· LLD

**状态**：已上线，真机验收未通过（2026-10-22 按用户指令暂停修复；SSE 代理与前端解析正常，失败点在 moon-well/magpie 150s 上游超时。代码保留）
**同源**：moon-well R196（后端 SSE + 在途去重）；承接 magicbook R190/R191、moon-well R192/R193

## 1. 问题与目标

写作批改是 70–150s 的同步 LLM 调用。R191 已把代理等待上限推到 210s，R193 已让同文 revise 幂等，但用户仍有两个体验问题：

1. 批改全程只有按钮转圈，用户不知道连接是否还活着、大概等了多久；
2. 任何中间层按 idle timeout 掐断，或部署切换中断长连接，前端只会看到 503 / 网络错误，且无法判断批改是否已经落库。

本轮把 magicbook 侧的批改主路径改为 SSE 进度流：后端持续发 `status` / `ping`，前端显示等待秒数；`result` / `error` 仍用统一 `Result` 信封；JSON 端点保留作为回退。**不改变批改结果、稿号规则与 R193 幂等语义**。

## 2. 端点与代理

`cps/routes/learning.py` 新增：

| magicbook 端点 | moon-well 端点 |
| --- | --- |
| `POST /ajax/learning/writing/submit/stream` | `POST /learning/writing/submit/stream` |
| `POST /ajax/learning/writing/revise/stream` | `POST /learning/writing/revise/stream` |

- 复用 `_b1_payload(("taskId","text"), ("taskId","text"))` 做白名单/长度校验；非法请求本地 400，不打后端。
- 通过 `cps.moonwell.client` 取 base URL、session token、trace id；`Authorization: Bearer …` 不下发浏览器。
- `requests.post(..., stream=True, timeout=(10, 300), proxies=NO_PROXY)`：10s 建连，300s 单 chunk idle；后端 5s 心跳远小于 idle，长批改不会被「整段 210s」限制。
- 建连阶段 401：`refresh_session_token()` 后关闭旧连接、用新 token 重连一次；流开始后不重放。
- 上游非 200：原样透传 body 与状态码（JSON 业务错误仍是 JSON），不伪装成空流。
- 200：`Response(stream_with_context(generator), content_type="text/event-stream")`，逐 chunk yield；附加 `Cache-Control: no-cache`、`X-Accel-Buffering: no`、`Connection: keep-alive`。
- 客户端断开：Flask 生成器退出，`finally` 关闭上游 requests；moon-well 批改线程不取消，结果继续落库。

## 3. 前端状态机

`cps/static/js/learning-writing.js`：

- `streamEndpoint()`：0 稿走 submit/stream，≥1 稿走 revise/stream；模板没注入 URL 时返回 null。
- `postSse()`：`fetch` + `response.body.getReader()` + `TextDecoder`，按 `\n\n` 切 SSE 帧，支持 `\r\n`；解析 `event:` / `data:`，`data` 多行用 `\n` 连接。**不用 `EventSource`**——需要 POST body 与 `X-CSRFToken`。
- `status` → 状态行「Reviewing…」；`ping` → 「Reviewing… Ns」，`elapsedMs` 由后端给，前端不自己猜。
- `result` → `resultOf({data: payload})` 解统一信封 → 既有 `renderReview`，更新 `writing.lastDraftNo`，刷新历史。
- `error` → 用 `Result.message` 直接展示；标记 `streamStarted=true`，不触发 JSON 回退。
- 回退：仅当 SSE 建连失败、HTTP 非 200、或**尚未收到任何事件**就断网时，自动走一次 JSON 端点；已收到 `status`/`ping` 后断网不重试。后端 R196 同文在途去重保证回退不会重复调 LLM。
- `finally`：释放 `busy()` 锁并按当前稿态刷新按钮文案；不引入自动重试。

模板 `learning_writing.html` 注入 `writingSubmitStream` / `writingReviseStream` 两个 URL。

## 4. 事件契约

```text
event: status
data: {"phase":"accepted"}

event: status
data: {"phase":"grading"}

event: ping
data: {"elapsedMs":5000}

event: result
data: {"success":true,"code":200,"result":{"submissionId":"9","draftNo":1,...}}

event: error
data: {"success":false,"code":50515,"message":"正文太短"}
```

建连前失败仍是 JSON：参数 400、未登录 401、moon-well 未配置/不可达 503。完整后端语义见 moon-well L2。

## 5. 测试与证据

- `tests/test_learning_writing_sse.py`（6）：登录、submit/revise 路径映射、payload 白名单、响应头、401 刷新重连、上游非 200 透传。
- `tests/test_learning_pages_static.py`（含新增 SSE 接线反向锁）：`postSse` / `getReader` / `streamStarted` / 两个 stream URL 必须存在，`new EventSource(` 不得出现。
- `tests/test_i18n_seed_contract.py`：新增 `Connection error` 种子词条与 po/mo 中文译文一致。
- 开发态合并闸门：`test_learning_proxy.py` + 上述三文件 **98 passed**（Python 3.8，2026-10-21）。
- 全量基线：`pytest -q` → **630 passed / 13 failed**；13 个失败全是既有 Python 3.8 / 缺书籍 fixture 基线（TTS、metadata outbound 等），本轮新增测试全部通过。
- 生产验收（2026-10-21 17:15，fnOS build END OK `4cded68c`；回填后 `bf45c23a` 再次 END OK）：magicbook 容器 `Up (healthy)`；线上 `learning-writing.js` 已含 `streamEndpoint` / `postSse` / `getReader`，模板已注入 `writingSubmitStream` / `writingReviseStream` 两个 URL。后端 SSE 直连实测见 moon-well R196 LLD：首条 ping 5.01s、result 前每 5s 一条、87.61s 返回 result；代理层 `X-Accel-Buffering: no` 与 401 刷新由 `test_learning_writing_sse.py` 的 6 条契约测试锁定。
- `node --check cps/static/js/learning-writing.js` 通过；`python3 -m py_compile cps/routes/learning.py` 通过。
- 真机验收：长文批改期间每 5s 看到等待秒数；完成后正常渲染；断网/刷新后历史仍能看到已保存结果；同文重试不多稿。
- **真机验收未通过（2026-10-22 09:29–09:32，用户 task=2 修订稿）**：浏览器 Network 命中 `POST /ajax/learning/writing/revise/stream`，`200 OK`，约 2.5min 后 UI 报错、Response 面板为空。moon-well 日志同一请求建连 37ms、150s 处 magpie `Read timed out` 并发出 SSE `error`；magpie 台账记录 `ms=150013,status=499`。结论：magicbook 的 SSE 代理与前端解析已生效，失败是后端 LLM 预算耗尽，不是代理缓冲或前端仍走旧 JSON 路径。
- **DevTools 读法**：SSE 响应体在 Network → Response 为空是正常现象，应看 EventStream/事件列表；UI 报错对应后端 `error` 事件，不能据此判定代理未透传。
- **生产配置未改**：moon-well 侧曾临时把 magpie 超时调到 240000，随后按“放弃修复”指令回滚为 150000；本仓代码无新增改动。

## 6. 风险与非目标

- SSE 不降低 LLM 延迟，也不绕过 magpie 150s 预算；它只把等待过程显式化并让连接更耐用。**2026-10-22 上游 150s 零 token 挂起仍会以 `error` 结束，本轮未解决。**
- blue-green 部署切换仍可能中断 SSE（Spring 25s shutdown / 容器 40s grace）；已完成的批改会落库，未完成的仍需重试。该 drain 窗口另项处理。
- 中间层必须不缓冲：代理已发 `X-Accel-Buffering: no`，Traefik/Caddy 当前未配置响应缓冲；若未来加 Nginx，需要同步关闭 `proxy_buffering`。
- 非目标：模型 token 级流式、异步 job + 轮询、自动跨版本重试。
