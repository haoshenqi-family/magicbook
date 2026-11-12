# MagicBook 工具型微信小程序

magicbook 的移动端入口：**每日复习 / 词汇量测试 / 我（学习数据）**。
阅读正文、翻译、朗读、AI 伴读仍在网页端（`magicbook.haoshenqi.top`）。
**生词本页面已于 R280 下掉**：小程序不再提供词汇列表入口，生词数据仍留在网页端；
词汇量测试交卷时仍会把不认识的词写进网页端生词本。

**AI 伴读已于 R292（2026-11-11）整体移除**：带 AI 对话能力的小程序过不了微信上架审核。
移除的是代码包里的全部相关件——对话页、tabBar 项、请求层的流式对话通道与对话专用超时，
不是只藏入口。后端的对话接口与网页端、浏览器扩展里的 AI 伴读都没动。
R280 / R283 的设计与实现记录保留在 `docs/project/iterations/2026-11-wx-ai-chat/`。

## 为什么是这三个

这三件事都是「掏出手机就能做完」的动作：刷一轮复习、测一次词汇量、看一眼数字。
阅读本身需要大屏与长注意力，放进小程序只会得到一个更难用的阅读器，所以边界仍是
**不渲染任何正文**。

## 数据与登录

- 直连后端 `moon-well.haoshenqi.top`（词汇数据、复习调度、词汇量测试、四股台账
  都在 moon-well，网页层只是代理）。
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
app.json                 页面与 tabBar（三个 tab + 登录/账号页）
config.js                baseUrl / 请求超时（换环境只改这里）
utils/api.js             请求层：Result 解包、401 单次刷新、失败原因透传
utils/auth.js            微信登录 / 邮箱认领 / 登录态
pages/login              微信一键登录 + 邮箱验证码认领
pages/review             每日复习：到期队列、四选一 / 拼写 / 回忆、四档自评
pages/test               词汇量测试：自适应作答、交卷、报告、推荐难度一键应用
pages/stats              我：身份卡、网页版入口、学习数据、退出登录
pages/account            账号：邮箱绑定、50512 二次确认
```

## 用到的后端接口

| 功能 | 接口 |
| --- | --- |
| 登录 | `POST /auth/wx/login`、`POST /auth/wx/email/{send-code,verify}`、`POST /auth/refreshToken` |
| 每日复习 | `GET /vocabulary/review/queue`、`POST /vocabulary/review/answer`、`GET /vocabulary/review/stats` |
| 词汇量测试 | `POST /vocabulary/test/{start,answer,finish}`、`GET /vocabulary/test/history` |
| 学习数据 | `GET /learning/plan/today`、`GET /learning/strands/summary` |
| 难度应用 | `POST /vocabulary/reading/settings/hard-level` |

## 已知边界

- **听辨题型不支持**：`/vocabulary/review/audio/{word}` 要带 JWT 头，小程序的音频组件无法
  自定义请求头。后端自 R238 起默认停出 `LISTEN_*`；万一出现会降级为「揭示后自评」，
  不会出哑题。
- **不做**：正文阅读、翻译、朗读、AI 伴读（R292 移除）、生词本列表、积分/充值、成就、站内信。
- **上传**：本机已装微信开发者工具（CLI 服务端口 13564）。带 `--info-output` 会触发 IDE
  `code 17 二维码输出路径无效` 报错，去掉即可。
