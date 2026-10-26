# learning · L2 接口说明

> 读者：调用者 / 集成者。magicbook 是每日学习前端，moon-well 是 learning 后端；本文件只维护「magicbook 端点 → moon-well 端点」的映射、超时与前端消费契约。后端语义的唯一权威是 moon-well 的 `docs/product/learning/interface.md`。

## 能力边界

每日学习中枢与八个学习子页面（复习队列、听写、口语陪练、复述训练、计时重读、写作工坊、单词编故事、选书难度匹配）的代理与前端接线。词汇、阅读、TTS 等相邻模块不在本文件范围。

本文件当前补齐 **写作批改 SSE（R194）** 与 **口语陪练语音优先（R221）** 两个子集；其余学习子功能仍以 `docs/product/readme/learning.md` 与 moon-well L2 为准，后续随演进补齐。

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
- **服务端也必须流式（R204）**：本仓用 tornado `WSGIContainer` 起 WSGI；tornado ≥6.3 的默认实现会把整段 body 收齐再一次性写出并补 `Content-Length`，SSE 会被整体缓冲、等待期零事件。`cps/tornado_wsgi.py` 因此对 `text/event-stream` 走专用流式分支（逐块写出、丢弃 `Content-Length`、阻塞读放在独立线程池，避免占住事件循环）。新增任何流式端点都自动受益，无需改路由。
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

## 口语陪练语音优先（R221）

### 1. 代理端点

| magicbook 端点 | moon-well 端点 | 超时 | 说明 |
| --- | --- | --- | --- |
| `POST /ajax/learning/speaking/session` | `POST /learning/speaking/session` | 210s | 开聊；响应含 `greetingAudioUrl` |
| `POST /ajax/learning/speaking/message` | `POST /learning/speaking/message` | 210s | 白名单 `sessionId/text/voice/audioObject/durationMs` |
| `POST /ajax/learning/speaking/report` | `POST /learning/speaking/report` | 210s | 会话报告；LLM 总结整场对话 |
| `POST /ajax/learning/speaking/recording/upload` | `POST /learning/speaking/recording/upload` | 30s | multipart `sessionId` + `file`，返回对象名 |
| `POST /ajax/learning/speaking/recording/audio` | `POST /learning/speaking/recording/audio` | 30s | `{sessionId,audioObject}` → 二进制音频 |
| `POST /ajax/learning/speaking/messages` | `POST /learning/speaking/messages` | 15s | 历史消息，含语音元数据 |
| `POST /ajax/reading-tts-cached` | `POST /tts/cached-audio` | 20s | 教练语音回读，不计费；miss 返回 404 |

### 2. 前端消费契约

- 教练开场与每轮回复先渲染语音条，原文默认折叠；点击「转文字」才展开。
- 用户停止录音后先调 `/ajax/learning/asr/transcribe`，把结果写进可编辑 textarea；
  只有点击发送才上传录音并调用 message。
- 录音上传 multipart 字段固定为 `sessionId` 与 `file`；代理本地先校验数字 sessionId、
  非空文件与 10MB 上限。
- 发送失败保留 `speaking.pending`、转写与已上传对象名；重试复用对象名，不重复上传。
- 音频回读是二进制，不能按 JSON `Result` 解包；错误时播放端显示失败提示。
- 口语开聊、每轮回复与会话报告统一给 210s 代理预算：moon-well 的 LLM 单项预算为
  120s，回复后还要同步合成教练语音；90s 会在后端仍成功时先被代理截成 503。

### 3. 词条与页面

- `learning-speaking.js` 的文案必须进 `i18n_seed.html` 与中文 PO，`messages.mo`
  由 PO 重新编译；页面必须声明 `speakingRecordingUpload`、`speakingRecordingAudio`、
  `readingTtsCached` 三条 URL。
- 教练自动播放只在开聊/发送后的用户手势链中尝试；历史回放不自动播放，避免浏览器策略
  造成失败弹窗。

## 计划设置与 banner 勾选（R208）

| magicbook 端点 | moon-well 端点 | 超时 | 说明 |
| --- | --- | --- | --- |
| `POST /ajax/learning/plan/settings` | `POST /learning/plan/settings` | 10s | 四股配比全量替换 + banner 勾选可选透传 |
| `GET /ajax/learning/plan/today` | `GET /learning/plan/today` | 15s | 今日计划；R208 起 `settings.bannerHiddenKeys` 随响应带回 |

- 请求体：`dailyNewLimit`（0-50）、`dailyMinutes`（5-240）、四股 `strand*Pct`（0-100，
  和=100 的校验在上游 50503）+ 可选 `bannerHiddenKeys: string[]`（banner 隐藏卡 key 列表）。
- `bannerHiddenKeys` 语义：**字段缺失 = 不改动既有勾选**（老客户端兼容，防止老前端保存
  四股时抹掉另一台设备配好的勾选）；空数组 = 显式全部显示；非空数组 = 隐藏这些卡。
  key 形制 `[a-z]{2,32}`、最多 10 个——形制违例本地 400 不打上游，业务违例由上游回 50525。
- 前端消费：中枢页 `learning-hub.js` 管理抽屉保存；`plan/today` 响应的
  `settings.bannerHiddenKeys` 用于打开页面时对齐勾选（localStorage 只作首屏镜像，
  服务端是真相）。

## 相关文档

- 用户手册：[learning](../readme/learning.md)
- 后端契约：moon-well `docs/product/learning/interface.md`
- 本次实现：[writing-sse LLD](../../project/iterations/2026-10-writing-sse/writing-sse/lld.md)
- 口语陪练语音优先：[r221-speaking-voice LLD](../../project/iterations/1.0/r221-speaking-voice/lld.md)

## 学习数据导出（R230，入口在个人页 /me）

| magicbook 端点 | moon-well 端点 | 超时 | 说明 |
| --- | --- | --- | --- |
| `POST /ajax/user-export/create` | `POST /export/learning-data` | 30s | 发起导出；本地校验密码 6-128 后仅透传 `{password}`，短密码本地 400 不触上游 |
| `GET /ajax/user-export/tasks` | `GET /export/learning-data/tasks` | 30s | 近 30 天任务列表（5s 轮询，有进行中任务时） |
| `GET /ajax/user-export/tasks/<id>/download` | `GET /export/learning-data/tasks/{id}/download` | 120s | **binary 透传**加密 ZIP + attachment 头；非 200 原样透传上游 Result 错误 |

- 前端：`/me` 面板（me.html + me.js 追加段），文案走 i18n 种子五步链（me.js 在 i18n_js_files 清单内）。
- 后端语义权威：moon-well `docs/product/export/interface.md`（错误码 50601-50605）。
- 密码只透传不落任何本仓存储；下载文件名 `my-learning-data-<id>.zip`。
