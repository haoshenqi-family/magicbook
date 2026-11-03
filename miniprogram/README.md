# MagicBook 工具型微信小程序

magicbook 的「词汇工具」部分搬到微信里：**生词本 / 每日复习 / 词汇量测试 / 学习数据**。
阅读、翻译、朗读、AI 伴读仍然留在网页端（`magicbook.haoshenqi.top`），这里不做。

## 为什么只做这四个

这四件事都是**标准列表交互**：翻页、筛选、点选、答题、看数字。它们恰好是「碎片时间想掏手机看
一眼」的动作，而阅读本身需要大屏与长注意力，放进小程序只会得到一个更难用的阅读器。
所以本小程序的边界是：**不渲染任何正文**，只消费网页端积累下来的词汇数据。

## 数据与登录

- 直连后端 `moon-well.haoshenqi.top`（生词本、复习调度、词汇量测试、四股台账都在 moon-well，
  网页层只是代理）。
- 登录 = 微信身份 + 一次账号绑定：
  1. 小程序 `wx.login` 拿 code → `POST /auth/wx/login`；
  2. 未绑定过的微信只会拿到一张 10 分钟票据，此时要求输入**网页端账号密码**完成绑定
     （`POST /auth/wx/bind`），之后永久免密。
  3. 绑定后拿到与网页端同一套 JWT（`authorization: Bearer …`），30 天有效，过期自动 refresh。
- 绑定不新建账号：账号里的生词本与复习进度是同一份，不存在「小程序里是一个新我」。

## 打开方式

1. 微信开发者工具 → 导入项目 → 目录选本文件夹（`magicbook/miniprogram`）。
2. AppID 已写在 `project.config.json`（`wxd511f98508dc9cee`）。
3. **服务器域名**：小程序后台 → 开发管理 → 开发设置 → 服务器域名 → request 合法域名
   添加 `https://moon-well.haoshenqi.top`。没配之前可在开发者工具「详情 → 本地设置」
   勾选**不校验合法域名**先跑通。
4. **后端密钥**：`/auth/wx/*` 需要 AppSecret 才能调 `jscode2session`。在 moon-well 的
   Nacos `moon-well-auth.yaml`（或环境变量）配置 `WX_SECRET`；没配时接口返回
   `50401 微信登录未配置`，这是配置缺失而不是登录失败。

## 目录

```
app.json                 页面与 tabBar（四个工具页 + 登录页）
config.js                baseUrl / 超时（换环境只改这里）
utils/api.js             请求层：统一解包 Result、401 单次刷新重试、错误抛出
utils/auth.js            微信登录 / 首次绑定 / 登录态
pages/login              微信登录 + 首次绑定表单
pages/notebook           生词本：分页、四个状态筛选、词前缀搜索、就地改标记
pages/review             每日复习：到期队列、四选一 / 拼写 / 回忆、四档自评
pages/test               词汇量测试：自适应作答、交卷、报告、推荐难度一键应用
pages/stats              学习数据：今日四股、复习摘要、近 7 天、最近词汇量
```

## 用到的后端接口

| 功能 | 接口 |
| --- | --- |
| 登录 | `POST /auth/wx/login`、`POST /auth/wx/bind`、`POST /auth/refreshToken` |
| 生词本 | `GET /vocabulary/notebook?page&size&filter&keyword`、`POST /vocabulary/mark` |
| 每日复习 | `GET /vocabulary/review/queue`、`POST /vocabulary/review/answer`、`GET /vocabulary/review/stats` |
| 词汇量测试 | `POST /vocabulary/test/{start,answer,finish}`、`GET /vocabulary/test/history` |
| 学习数据 | `GET /learning/plan/today`、`GET /learning/strands/summary` |
| 难度应用 | `POST /vocabulary/reading/settings/hard-level` |

## 已知边界

- **听辨题型不支持**：`/vocabulary/review/audio/{word}` 要带 JWT 头，小程序的音频组件无法
  自定义请求头。后端自 R238 起默认停出 `LISTEN_*`，队列里正常不会出现；万一出现会降级为
  「揭示后自评」，不会出哑题。
- **释义依赖缓存**：生词本的释义来自单词详解缓存，没在网页端查过的词释义为空，列表显示
  「暂无释义」而不是现场生成（生成要计费）。
- **不做**：正文阅读、翻译、朗读、AI 伴读、积分/充值、成就、站内信。
