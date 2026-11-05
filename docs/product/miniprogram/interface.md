# miniprogram 模块 · 接口说明（L2）

> 读者：小程序与后端集成者。只讲「功能定义 + 功能说明 + 调用方法」，实现与边界见
> [L3 实现说明](features/ai-chat.md)；本次怎么实现见
> [R280 LLD](../../project/iterations/2026-11-wx-ai-chat/r280-miniprogram-ai-chat/lld.md)。
> 后端契约的**唯一权威**是 moon-well `docs/product/system/interface.md` §7，本页是消费侧登记。

## 1. 模块边界

小程序**直连** `moon-well.haoshenqi.top`，不经 magicbook Python 侧代理：复习、词汇量测试、
账号等普通请求走统一 `Result{success, result, message}` 解包（见 `miniprogram/utils/api.js`）；
**AI 伴读是唯一例外**——它是 `text/event-stream` 流式响应，必须单独一条通道。

R280 起 tab 为「复习 / 伴读 / 词汇量 / 我」。`pages/notebook` 已删除，
词汇量测试报告里的「收进生词本」指的是**网页端**生词本，数据面未改。

## 2. AI 伴读对话：`POST /ai/agent/chat`（SSE）

### 功能定义

在小程序里发起一轮不绑定书籍 / 网页的通用对话，回答以 SSE 逐字返回。

### 请求

| 项 | 值 |
| --- | --- |
| Method / Path | `POST https://moon-well.haoshenqi.top/ai/agent/chat` |
| 鉴权 | 请求头 `authorization: Bearer <accessToken>`（与普通请求同一套 JWT；失效时刷新一次重试） |
| 头 | `content-type: application/json`、`Accept: text/event-stream` |
| 超时 | 180000 ms（`config.js` 的 `chatTimeout`，明显长于普通请求的 15000 ms） |
| 传输 | `wx.request` 的 `enableChunked: true` + `onChunkReceived`，`responseType: arraybuffer` |

请求体（**字段白名单**：除下表外不传任何书籍 / 网页上下文字段）：

```json
{
  "conversationId": 12345,
  "message": "这个词怎么用在句子里？",
  "scene": "general",
  "skipMemoryExtract": true
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `message` | 是 | 本轮用户输入，后端上限 4000 字符 |
| `scene` | 是 | 固定 `general`；服务端据此加载 `agent-chat-system-general`（moon-well R243） |
| `conversationId` | 否 | 空 = 新建会话；服务端把新建的 id 经 `final` 事件回传 |
| `skipMemoryExtract` | 否 | 小程序固定 `true`：通用闲聊默认不抽取长期记忆 |

**不得携带**：`bookId` / `bookTitle` / `authors` / `chapter` / `pageText` /
`unfamiliarWords`。小程序里没有书页上下文，传了只会让模板渲染出假上下文；
`scene=general` 下服务端也不使用这些变量。

### 响应（SSE 事件）

每帧形如 `event: <name>\ndata: <JSON>\n\n`。小程序消费四类：

| event | data | 界面动作 |
| --- | --- | --- |
| `delta` | `{ "text": "…", "data": "…" }` | 追加到当前回答气泡，状态 `streaming` |
| `tool_call` | `{ "step", "name", "argsSummary", "requireConfirm" }` | 尚无正文时把「正在思考」换成「正在查证」 |
| `final` | `{ "conversationId", "messageId", "status", "usage" }` | 持久化 `conversationId` 到 `mb.chat.conversationId` |
| `error` | `{ "message", "code" }` | 气泡内显示错误 + toast |

`tool_result` / `audio` 事件服务端仍会下发，小程序**不渲染、不自动播放音频**。

### 失败形态

- HTTP 401 / 403：**仅在流尚未开始时**刷新 token 并重试一次；流已开始则不再重放（会重复出字、重复计费）。
- HTTP ≥ 400：解析响应体 `message`，原样提示；解析失败回落 `请求失败（HTTP <code>）`。
- `wx.request` 的 `fail`：保留原始 `errMsg`，并区分白名单（带运行时 AppID，R281）、超时、SSL/链路错误。
- 流中途 `error` 事件或流结束时仍无正文：气泡显示「这次没有收到回复，请重试」。

## 3. 会话状态

- `conversationId` 只存小程序本地 `mb.chat.conversationId`；「新会话」只清本地 id 与界面消息，
  **不删服务端历史**（历史仍挂账号，可在网页端查看）。
- 换设备 / 重进小程序会带走同一个本地 id；账号切换后本地 id 可能指向他人不可见的会话，
  此时服务端按权限处理，客户端不会因此崩溃。

## 4. 部署顺序（强约束）

> 2026-11-05 回填：后端 moon-well R243 已上线（10:13:04 deploy SUCCESS，
> `agent-chat-system-general@1.0.0` 在线且正文校验通过），顺序约束的前半段已完成；
> 小程序体验版待开发者工具 CLI 服务端口开启后上传。

1. **先上线 moon-well R243**：`scene` 分支 + `agent-chat-system-general` 必须先在现网可用。
   新 prompt 现网缺失时由 `NacosPromptBootstrap` 在后端启动自检里 `create + publish`（已在线则跳过），
   上线后应回读 Nacos prompt 列表与版本确认在线。
2. **再发布小程序体验版**：旧后端不认识 `scene` 时会按 `bookId == null` 落到网页伴读 prompt，
   用户会看到「当前页面正文摘录」这类小程序里根本不存在的上下文。

## 5. 其余端点

复习 / 词汇量 / 账号 / 学习数据仍是普通 JSON 请求，契约以 moon-well 对应模块 L2 为准；
小程序侧统一走 `utils/api.js` 的 `request()`（含一次 401 刷新与 `Result` 解包）。
