# miniprogram 模块 · 接口说明（L2）

> 读者：小程序与后端集成者。只讲「功能定义 + 功能说明 + 调用方法」，实现与边界见
> [L3 每日复习卡片](features/review.md)。
> 后端契约的**唯一权威**是 moon-well 对应模块的 L2，本页是消费侧登记。
>
> **R292（2026-11-11）改写**：本页原先的主体是 AI 伴读对话 `POST /ai/agent/chat` 的 SSE 契约
> （R280 建）。带 AI 对话能力的小程序过不了微信上架审核，对话页与流式通道已整体移除，
> 小程序**不再调用** `/ai/agent/chat`，相应章节随之删除。那份契约的原文见
> `git show 5a49872f:docs/product/miniprogram/interface.md`；接口本身仍在 moon-well，
> 由网页端与浏览器扩展使用，权威定义见 moon-well `docs/product/system/interface.md` §7。

## 1. 模块边界

小程序**直连** `moon-well.haoshenqi.top`，不经 magicbook Python 侧代理（网页代理依赖 Flask 会话，
小程序没有）。所有请求都是普通 JSON，统一走 `miniprogram/utils/api.js` 的 `request()`：
`Result{success, result, message}` 解包、401 时刷新一次 token 并重试、失败原因透传。

底栏三项「复习 / 词汇量 / 我」，另有登录页与账号页。`pages/notebook`（R280）与
`pages/chat`（R292）均已删除；词汇量测试报告里的「收进生词本」指的是**网页端**生词本。

## 2. 调用约定

| 项 | 值 |
| --- | --- |
| Base URL | `https://moon-well.haoshenqi.top`（`config.js` 的 `baseUrl`，须在该 AppID 的 request 合法域名里） |
| 鉴权 | 请求头 `authorization: Bearer <accessToken>`；登录类端点不带 |
| 头 | `content-type: application/json` |
| 超时 | 15000 ms（`config.js` 的 `timeout`，全部请求同一个值） |
| 响应 | `Result{success, result, message}`；`success=false` 时 `message` 原样提示 |

失败形态：

- HTTP 401：刷新 token 后重试一次；刷新失败清本地登录态并回登录页。
- `wx.request` 的 `fail`：保留原始 `errMsg`，带出实际请求的完整 URL 与运行时 AppID，
  并区分白名单、超时、SSL / 链路错误（R277 / R281 / R282）。

## 3. 端点清单

| 功能 | 接口 |
| --- | --- |
| 登录 | `POST /auth/wx/login`、`POST /auth/wx/email/{send-code,verify}`、`POST /auth/refreshToken` |
| 密码绑定（兜底，界面不暴露，R273） | `POST /auth/wx/bind` |
| 账号绑定邮箱 | `POST /auth/email/send-code`、`POST /auth/email/verify` |
| 每日复习 | `GET /vocabulary/review/queue`、`POST /vocabulary/review/answer`、`GET /vocabulary/review/stats` |
| 词汇量测试 | `POST /vocabulary/test/{start,answer,finish}`、`GET /vocabulary/test/history` |
| 难度应用 | `POST /vocabulary/reading/settings/hard-level` |
| 学习数据 | `GET /learning/plan/today`、`GET /learning/strands/summary` |

各端点的请求 / 响应字段以 moon-well 对应模块 L2 为准，这里不复制。
