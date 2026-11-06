# LLD · R271 微信小程序（工具型）：生词本 / 每日复习 / 词汇量测试 / 学习数据

- **状态**：开发中（工程与四页 UI 已完成，未在真机/开发者工具编译验证；见 §7）
- **迭代**：1.0　**需求编号**：R271（后端同源 moon-well R239）
- **新增目录**：`magicbook/miniprogram/`（原生小程序，无框架、无云开发）

## 1. 需求与边界

用户口径：「工具型小程序——生词本 / 每日复习 / 词汇量测试 / 学习数据，阅读留在网页；最低，
全是标准列表交互」。

据此定的边界：

| 做 | 不做 |
| --- | --- |
| 四个工具页 + 微信登录 | 正文渲染、阅读器、翻译、朗读、AI 伴读 |
| 复用 moon-well 现有词汇/学习/测试接口 | 新增业务逻辑（唯一新增是后端两个接口，见 moon-well R239） |
| 原生小程序（`app.json` + 4 页 + tabBar） | 云开发/云数据库（数据已经在 moon-well，不建第二份） |

**为什么不做小程序版阅读器**：阅读需要长注意力与大屏，小程序里只会得到一个更差的阅读器；
而这四件事恰好是「掏手机看一眼/刷几张卡」的动作。边界写进 L1 `miniprogram.md`，避免后续被
「顺手也加个阅读吧」反复拉扯。

## 2. 为什么直连 moon-well 而不是走 magicbook 代理

网页端的词汇代理（`/ajax/learning/srs/*` 等）依赖 magicbook 的登录会话（Flask session +
OIDC），小程序里没有这个会话，要走代理就得在 magicbook 侧再实现一套小程序登录。

而数据本来就在 moon-well：生词本、复习调度、词汇量测试、四股台账全部出自那里，网页只是薄代理。
小程序直连后端少一跳、少一处会话依赖。代价是**小程序后台必须把 `moon-well.haoshenqi.top`
加进 request 合法域名**（部署步骤见 §6）。

## 3. 登录

两步式（后端见 moon-well R239 LLD，这里只说客户端）：

```
wx.login → code → POST /auth/wx/login
  ├ 已绑定：拿 accessToken/refreshToken → 落 storage → switchTab 生词本
  └ 未绑定：只拿 bindTicket（10 分钟）→ 就地展开账号密码表单
        → POST /auth/wx/bind → 拿 token → switchTab 生词本
```

- 表单**就在登录页展开**，不跳新页：票据 10 分钟过期，多一次跳转就多一次失败面。
- 票据过期（50403）时把表单收回去，逼用户重新走一次微信登录拿新票据。
- token 存 `wx.setStorageSync`；401 时用 refreshToken 换一次再重试原请求，刷新用模块级
  promise 去重（四个 tab 同时 401 不能打四发 refresh）。
- 登录态失效 → `clearSession` + `reLaunch` 登录页，不留在页面上显示空数据。

## 4. 页面与数据

| 页面 | 数据源 | 关键交互 |
| --- | --- | --- |
| `pages/notebook` | `GET /vocabulary/notebook`、`POST /vocabulary/mark` | 四状态 chips（带角标）、词前缀搜索、上滑加载更多、点词 actionSheet 改标记 |
| `pages/review` | `GET /vocabulary/review/queue`、`POST /vocabulary/review/answer`、`GET /vocabulary/review/stats` | 一卡一答；四选一/拼写/回忆三态；揭示后四档自评；答完自动下一张，队列走完出「继续加练」 |
| `pages/test` | `POST /vocabulary/test/{start,answer,finish}`、`GET /vocabulary/test/history`、`POST /vocabulary/reading/settings/hard-level` | idle → 答题 → 交卷确认（含「收进生词本」开关）→ 报告 → 一键应用推荐难度 |
| `pages/stats` | `GET /learning/plan/today`、`GET /vocabulary/review/stats`、`GET /learning/strands/summary`、`GET /vocabulary/test/history` | 四股进度条、复习摘要五格、近 7 天堆叠条、最近词汇量；退出登录 |

设计要点：

- **题型降级链**：`CHOOSE`/`DISCRIMINATE` 有释义且有选项才出四选一；`SPELL` 有释义才出拼写；
  其余（含 `RECALL`、`CONTEXT_CLOZE`、`LISTEN_*`）走「揭示后自评」。**释义缺失绝不硬出题**
  （题干是空的，用户只能瞎点）。
- **始终回传原始题型**：`answer` 请求带的 `questionType` 是后端下发的那个，不是本地降级后的
  呈现态——它进 `word_event`，是四技能统计与保持率的底座。
- **判对错不代替自评**：四选一选对也照样要按四档自评，因为 grade 才决定下次出现时间。
- **生词本只列有标记的词**（后端口径），释义只读缓存；列表里没释义就显示「暂无释义」，
  不给「现场生成」的路径（会消耗积分）。

## 5. 错误可见性

- 网络失败、业务失败、鉴权失败统一抛 `{code, message}`，页面 `toast` 出**后端原文**，
  绝不静默显示成空列表——「静默降级会把接口故障伪装成数据不存在」（家族纪律）。
- 统计页四个请求各自 `catch`：单块失败只在该块显示红字「加载失败」，其他块照常渲染；
  **失败不会写成 0**（0 和「拿不到」是两件事）。
- 生词本筛选传非法值时后端返回 400，前端不改写、不重试（说明客户端有 bug，应修而不是兜）。

## 6. 部署与验证

1. 微信开发者工具 → 导入项目 → 目录选 `magicbook/miniprogram`；AppID 已写在
   `project.config.json`（`wxd511f98508dc9cee`）。
2. 小程序后台 → 开发管理 → 开发设置 → 服务器域名 → request 合法域名加
   `https://moon-well.haoshenqi.top`。**没配之前**可在「详情 → 本地设置」勾选
   「不校验合法域名」跑通开发。
3. moon-well 侧需先满足（见那边 R239 部署节）：`app_user_wechat` 表已建、`app.wx.secret`
   已配。否则 `/auth/wx/*` 会返回 50401，登录页会显示「微信登录未配置，请联系管理员」。
4. 小程序不参与 magicbook 容器构建：`miniprogram/` 是纯静态源码目录，`Dockerfile` 不 COPY
   它，`cps/` 不引用它。**push develop 只影响网页服务，不会把小程序带上线**；小程序上线走
   微信开发者工具上传 + 提审。

## 7. 验证情况（如实记录）

- 已做：全部 `.js` 通过 `node --check`；全部 `.json` 通过 `JSON.parse`；接口路径逐个比对
  moon-well 控制器与 DTO 字段。
- **未做**：本机未安装微信开发者工具，**没有编译/模拟器/真机运行过**。首次打开可能出现的
  问题集中在两处——`app.json` 的 tabBar（本次为纯文字 tab，无图标资源）与 WXML 表达式
  （`counts[item.key]`、三元嵌套）。这两处需要真机/模拟器确认。
- 后端接口在未部署 R239 前全部 404/50401，属预期。

## 8. 已知边界（写进 L1 的部分再次在此钉住）

- 听辨题型（`LISTEN_CHOOSE`/`LISTEN_SPELL`）不支持：音频端点要 JWT 头，小程序音频组件无法
  自定义请求头；后端 R238 起默认停出，正常不出现，万一出现降级为「揭示自评」。
- 不做解绑/换账号入口：换微信需在新微信重新绑定一次（后端支持覆盖旧绑定）。
- 不做积分/充值/成就/站内信：工具型的边界就是四页，多一页就多一份维护面。
