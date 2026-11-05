# MagicBook 工具型微信小程序

magicbook 的移动端入口：**AI 伴读 / 每日复习 / 词汇量测试 / 我（学习数据）**。
阅读正文、翻译、朗读仍在网页端（`magicbook.haoshenqi.top`）。
**生词本页面已于 R280 下掉**：小程序不再提供词汇列表入口，生词数据仍留在网页端；
词汇量测试交卷时仍会把不认识的词写进网页端生词本。

## 为什么是这四个

这四件事都是「掏出手机就能做完」的动作：聊两句、刷一轮复习、测一次词汇量、看一眼数字。
阅读本身需要大屏与长注意力，放进小程序只会得到一个更难用的阅读器，所以边界仍是
**不渲染任何正文**。AI 伴读是其中的例外：它是对话，不是阅读器，天然适合手机。

## AI 伴读（通用对话）

- 入口：tabBar「伴读」。直连 moon-well `POST /ai/agent/chat`（SSE 流式），
  请求带 `scene: 'general'` 并置 `skipMemoryExtract: true`，**不传** `bookId` /
  `bookTitle` / `pageText` / `unfamiliarWords`。
- 后端按 `scene=general` 加载 `agent-chat-system-general`（Nacos Prompt Registry，
  moon-well 启动自检 create + publish）。这把通用 prompt 没有书名、章节、当前页原文、
  本页生词，也不假设用户手边有文本；记忆、用户自我介绍、伙伴名照常注入。
  需要书籍上下文的工具（`add_annotation` / `list_annotations` /
  `get_paragraph_translation`）不下发给模型。
- 会话 `bookId=0`，与网页端「站点会话」同源；`final` 事件回传的 `conversationId`
  存在 `mb.chat.conversationId`，续聊自动带上。「新会话」只清本地 id，历史不删，
  可在网页端查看；小程序本身不提供历史列表。
- 流式实现在 `utils/api.js#chatStream`：`wx.request` 的 `enableChunked` +
  `onChunkReceived`，自带 UTF-8 分块解码（一个汉字可能跨两个片段）、SSE 分帧解析、
  连接建立阶段 401 单次刷新（流开始后绝不重放）。**基础库 2.20.0+** 才有
  `onChunkReceived`；低版本退化为一次性读取完整响应体。
- 超时：`config.chatTimeout = 180000`（3 分钟，对齐 agent 有界循环）；普通请求 15s。
- 小程序不展示工具轨迹、不自动播放朗读音频；`tool_call` 只把气泡状态从「正在思考」
  换成「正在查证」。
- **部署顺序**：moon-well R243（新 prompt + `scene` 分支）先上线，再发小程序。
  **2026-11-05 进度**：后端已上线（10:13:04 fnOS 蓝绿部署 SUCCESS，
  `agent-chat-system-general@1.0.0` 在线、正文与代码模板逐字一致）；小程序体验版待上传。
  旧后端会忽略 `scene` 字段、按 `bookId=null` 走网页助手 prompt，出现「正在浏览网页」
  这类错误措辞。

## 数据与登录

- 直连后端 `moon-well.haoshenqi.top`（词汇数据、复习调度、词汇量测试、四股台账与
  AI 伴读 agent 都在 moon-well，网页层只是代理）。
- 登录（R240 / R241 现行口径）：
  1. `wx.login` 拿 code → `POST /auth/wx/login`；未绑定过的微信**自动建一个微信临时账号**
     并直接下发 JWT，无需输密码；
  2. 已有网页端账号用「我已有账号，用邮箱登录」：`/auth/wx/email/send-code` +
     `/auth/wx/email/verify` 收验证码认领，邮箱无账号返回 `50514` 且不建号；
  3. JWT（`authorization: Bearer …`）过期由 `utils/api.js` 统一刷新一次，失败才回登录页。

## 打开方式 / 工程信息

| 项 | 值 |
| --- | --- |
| 导入目录 | `magicbook/miniprogram`（原生小程序，无框架、无云开发） |
| AppID | `wx7b31b435be6beae3`（`project.config.json`，R276 起的正式号） |
| 后端 | `https://moon-well.haoshenqi.top` |
| 网页端 | `https://magicbook.haoshenqi.top`（阅读、书库、笔记、生词本） |
| request 合法域名 | `https://moon-well.haoshenqi.top`（按 AppID 配置，换号要重配） |
| 后端密钥 | Nacos `moon-well-auth.yaml` 的 `app.wx.secret`，不入仓；未配返回 `50401` |

- **体验版严格校验合法域名**：开发者工具「不校验合法域名」只对开发版生效（R277）。
  请求失败时 `utils/api.js` 会透传 `errMsg` 并区分「白名单 / 超时 / 链路」三类，
  真机可用 vConsole 看 `console.error` 留痕。
- openid 是 AppID 维度的；换 AppID 必须同步换 AppSecret，首次登录会落到新账号，
  用邮箱登录认领老账号。

## 目录

```
app.json                 页面与 tabBar（四个 tab + 登录/账号页）
config.js                baseUrl / 普通超时 / 对话超时（换环境只改这里）
utils/api.js             请求层：Result 解包、401 单次刷新、SSE 流式 chatStream
utils/auth.js            微信登录 / 邮箱认领 / 登录态
pages/login              微信一键登录 + 邮箱验证码认领
pages/chat               AI 伴读：通用对话、流式气泡、新会话
pages/review             每日复习：到期队列、四选一 / 拼写 / 回忆、四档自评
pages/test               词汇量测试：自适应作答、交卷、报告、推荐难度一键应用
pages/stats              我：身份卡、网页版入口、学习数据、退出登录
pages/account            账号：邮箱绑定、50512 二次确认
```

## 用到的后端接口

| 功能 | 接口 |
| --- | --- |
| 登录 | `POST /auth/wx/login`、`POST /auth/wx/email/{send-code,verify}`、`POST /auth/refreshToken` |
| AI 伴读 | `POST /ai/agent/chat`（SSE，`scene=general`） |
| 每日复习 | `GET /vocabulary/review/queue`、`POST /vocabulary/review/answer`、`GET /vocabulary/review/stats` |
| 词汇量测试 | `POST /vocabulary/test/{start,answer,finish}`、`GET /vocabulary/test/history`、`POST /vocabulary/mark` |
| 学习数据 | `GET /learning/plan/today`、`GET /learning/strands/summary` |
| 难度应用 | `POST /vocabulary/reading/settings/hard-level` |

## 已知边界

- **听辨题型不支持**：`/vocabulary/review/audio/{word}` 要带 JWT 头，小程序的音频组件无法
  自定义请求头。后端自 R238 起默认停出 `LISTEN_*`；万一出现会降级为「揭示后自评」，
  不会出哑题。
- **不做**：正文阅读、翻译、朗读、生词本列表、积分/充值、成就、站内信、会话历史列表。
- **真机待验**：`enableChunked` 的流式表现在不同基础库/机型上需上传体验版实测；
  本机无微信开发者工具，本轮只做静态校验与 `node --check`。
