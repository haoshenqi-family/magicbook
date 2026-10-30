# LLD — R251 MagicBook UI 信息架构、导航分组与账号/管理 L2 拆页

> 状态：**已上线待验收（第二轮）**（2026-10-29；第一轮 `70aa636c` 已上线；本轮补账号/管理 L2 拆页、完整功能树与长期原则）
> 工作项：R251 · 迭代 1.0
> 需求基线：[library requirements](../../../../product/library/requirements.md) · 验收：[acceptance.md](./ac/acceptance.md)

## 1. 用户原话与目标

> 「目前的UI系统有一点乱，帮我设计一个更好看更合理的分组，显示。并总结经验教训，设计原则。以后按照这个来。
> magicbook 的UI系统，尽量少修改 calibre 的UI系统。
> 1. 先按照你的设计做一版，我看一下效果」

本轮只做第一版可验收原型，不重写 Calibre-Web：

1. 顶栏收敛成五个一级域，页面不再靠堆入口表达功能。
2. 侧栏把 Browse、书架、分级、媒体、系统分层，减少平铺造成的认知负担。
3. 每个页面最多点亮一个一级域，未知页面不冒充书库。
4. 展示分组必须安全兜底，规则识别不到的书架仍然完整出现。
5. 把可复用的信息架构原则沉淀为长期 KB，后续 UI 任务按同一套原则评审。

## 2. 信息架构

### 2.1 一级域

| 一级域 | 入口 | 主要任务 |
| --- | --- | --- |
| 首页 | `/home` | 今天读什么、继续阅读、今日计划 |
| 书库 | `/` 及 Calibre 书目页 | 浏览、搜索、筛选、查看详情、阅读 |
| 学习 | `/learning/*` | 复习、听说读写等日常学习 |
| 账号 | `/me`、积分、伙伴、邮件、阅读设置 | 个人偏好、资产、消息 |
| 管理 | `/admin/*` | 系统配置、用户与运营工具 |

Settings 下拉仍是工具容器，但不再承载与书库并列的一级「管理」入口。管理员入口移入左侧主导航，
普通用户看不到管理域。

### 2.2 侧栏

```text
Browse       Calibre 原书目浏览项
Shelves      用户自建、无法归入其他规则的书架
Levels      “阶N / 分级阶 N”书架，按数字升序
Media       TED / Audio / Listening / 音频 / 听力书架
System      创建书架、关于等低频系统入口
```

- 分组只影响侧栏展示，**不新增 `Shelf.kind`，不迁移 schema**。
- 识别不出规则的书架进入 `Shelves` 兜底组；任何书架入口都不能因分类而消失。
- 每个非空书架组显示数量徽标；空组不渲染标题。
- CaliBlur 主题下 `System` 标题隐藏，因为该主题自己承接“创建书架/关于”的布局；
  其余分组标题保留紧凑节奏，不再继承 Calibre 的 60px 导航项高度。

## 3. 实现

### 3.1 产品层规则

新增 `cps/ui_ia.py`，把判断从 vendored 模板逻辑中拆出：

```python
shelf_nav_group(name)       # levels / media / shelves
shelf_level_sort(shelves)   # 阶1 < 阶2 < 阶10
nav_domain(path, page)      # home / library / learning / account / admin / ""
```

`cps/jinjia.py` 只新增 1 个 import、3 个模板过滤器注册，不把产品规则写进 Calibre-Web 路由。

### 3.2 模板

`cps/templates/layout.html`：

- 主导航统一为 `首页 / 书库 / 学习 / 账号 / 管理`；
- 保留 `top_home`、`top_library`、`top_learning`、`top_me`、`top_admin` 等既有 DOM ID；
- 以 `current_domain` 单一值驱动 `active` 与 `aria-current="page"`；
- Calibre Browse 项只在当前域确实为书库时点亮；
- 移动底栏复用同一域判定，不再维护第二套页面名单；
- 移动底栏第四项固定显示“账号”，不直接渲染可能过长的用户名；
- 书架按展示规则分组并显示数量，创建书架/关于归入系统组。

### 3.3 样式

`cps/static/css/magicbook.css` 只做增量样式：

- 主导航用细下划线与品牌绿表达 active；
- 分组标题用小竖条、紧凑间距和数量徽标形成层级；
- 平板宽度缩减主导航水平内边距，保证五域仍可见；
- 移动底栏用四列 flex，覆盖 Bootstrap `.visible-xs { display:block!important }`；
- 移动悬浮球用 `body #ai-companion-fab-wrap` 提高一级特异度，保证不被后加载的
  `ai_chat.css` 覆盖回底栏区域。

未修改 `cps/static/css/caliBlur.css`、`style.css` 等 vendored Calibre 样式。

### 3.4 文案

中文 PO/MO 增加：

| msgid | 中文 |
| --- | --- |
| `Levels` | 分级 |
| `Media` | 媒体 |
| `System` | 系统 |

## 4. 归属与兜底

`nav_domain()` 按“更具体路径优先”的顺序判断：

```text
/home                  -> home
/learning*             -> learning
账号路径白名单          -> account
/admin*                -> admin
Calibre 书目 page/path -> library
其他                    -> ""
```

关键边界：

- `/reading/settings` 属于账号，不属于书库；Calibre 的 Books List 不再误亮。
- `/stats`、`/login` 等未知页面不命中任何一级域，不强行点亮书库。
- 阅读页 `/read/<id>` 属于书库域，保持上下文连续。
- 规则调整时先补 `nav_domain()` 单测，再改模板；模板不维护第二份路径名单。

## 5. 兼容与最小侵入

- 不重写 Calibre 的 Bootstrap 3 导航骨架，只在既有 `<ul>` 上增加 `mb-primary-nav`。
- 不改 Calibre 的 sidebar 数据源，只在渲染阶段消费 `g.shelves_access`。
- 不改 `ub.Shelf` schema，不引入数据库迁移。
- 保留现有 DOM ID，避免 onboarding、测试和脚本锚点漂移。
- CaliBlur 只做产品层覆盖，不编辑主题源文件。

## 6. 验证

定向回归：

```text
tests/test_home_nav_shell.py
12 passed / 0 failed / 2 warnings
```

覆盖：

- 五个一级域都进入主导航；
- 账号页只点亮账号域，不点亮书库；
- Calibre Books List 不在账号页误 active；
- 分级/媒体/默认书架分类与 `阶1 < 阶2 < 阶10`；
- 未知页面不归属一级域；
- 真实渲染中书架入口数量守恒；
- 移动底栏与悬浮球安全区规则存在。

真实 Chromium：

| 视口 | 结果 |
| --- | --- |
| 1440×1200 | 无横向滚动；账号域唯一 active；书架分组与数量可见 |
| 390×844 | `scrollWidth == innerWidth`；底栏四列；悬浮球底部 780px、底栏顶部约 795px，无重叠 |
| 1440×1200 CaliBlur | 无横向滚动；系统空标题不渲染；分组标题高度收紧 |
| 390×844 CaliBlur | 无横向滚动；底栏与悬浮球不重叠 |

`git diff --check` 与 `py_compile cps/ui_ia.py cps/jinjia.py` 通过。

正式发布态：

```text
pytest tests/ -q
1188 passed / 0 failed / 4 warnings
```

发布验证：

- `48327926..70aa636c` 已推送 `origin/develop`；
- fnOS `build END OK (70aa636c58df969e68ce80ec55dcfcee01b8dc38)`；
- app-manager `deploy SUCCESS`，容器 `running / healthy`；
- `house.build-sha=70aa636c58df969e68ce80ec55dcfcee01b8dc38`，
  `house.code-digest=165b49e82f6aa555`；
- 本机与生产 `/login` 均为 HTTP 200。生产登录态未保留，`/reading/settings`
  正确 302 到登录页，因此桌面/移动视觉证据以本地真实模板 Chromium 验收为准。

## 7. 后续边界

- 本轮是分组原型，不改书架的业务语义。
- 只有当真实业务需要“用户显式指定书架类型、排序、权限”时，才评估 `shelf.kind`；
  仅为了当前展示分组不引入 schema。
- 后续新增一级域前必须先回答：它是否有独立任务、是否与现有域互斥、移动端第 5 个入口是否仍可容纳。
- 信息架构改动必须同时具备归属单测、入口守恒测试和桌面/移动视口检查。

## 8. 文档四问

- 能力变了：L1 `docs/product/readme/library.md` 增加五域导航、书架分组和移动底栏说明。
- 契约变了：无对外 HTTP 契约变化。
- 实现/边界变了：L3 `docs/product/library/features/ui-information-architecture.md`。
- 本次怎么实现：本 LLD 与同目录 AC；长期原则见
  `docs/kb/instructions/coding/ui-information-architecture.md`。

## 9. 第二轮用户补充

> 「先找到 magicbook（非 calibre 的部分）所有的功能（小功能，比如单词难度设置和单词量测试算两个功能），
> 然后列出来。把这些功能分类，分级，列出树状结构。A 账号的各个 L2 现在都堆在一个页面，
> 过于拥挤，改成类似 S 学习的 L2，不用卡片，但是不要把多个 L2 放在一起。
> M 管理也跟 A 账号一样改造一下。按照以上讨论，重新整理一下 UI 功能路由和排列方式。」

第一轮解决了“顶栏 + 侧栏 + active”外壳问题，但账号与管理仍有两个结构性缺陷：

1. 账号能力分散在 `/me`、Settings、伙伴页和积分页，`/me` 自己还堆了难度、主题、伙伴、导出；
2. 管理只有旧仪表盘与零散入口，没有稳定、可枚举的 L2 路由。

第二轮把“功能发现”改成“先建功能树，再一页一任务”，并把长期原则固化为以后 UI 需求的评审入口。

## 10. 功能树与路由定稿

完整 MagicBook 非 Calibre 功能地图落在 L1
[`feature-map.md`](../../../../product/readme/feature-map.md)，并由产品 README 引用。
树按用户任务分为首页、书库增强、阅读器增强、词汇、学习、伙伴与 AI 伴读、账号、管理八支；
叶节点是可独立理解和操作的“小功能”，例如难度档位与词汇量测试分别成叶。
L3 [`ui-information-architecture.md` §4](../../../../product/library/features/ui-information-architecture.md#4-功能地图与页面归属)
只保留页面归属、权限边界与测试要求，不再复制整棵树。

账号 A1–A7：

| 编号 | 路由 | 单页任务 |
| --- | --- | --- |
| A1 | `/me` | 资料、OIDC 绑定、界面/书籍语言 |
| A2 | `/buddy` | 伙伴花名册、装备、快捷动作、AI 伴读入口 |
| A3 | `/mail` | 站内信收件箱 |
| A4 | `/reading/settings` | 难度、词汇量测试/细筛、主题、使用引导 |
| A5 | `/credits` | 用户余额、充值、积分卡、明细 |
| A6 | `/achievements` | 成就 |
| A7 | `/me/export` | 学习数据导出 |

管理 M1–M13：

| 编号 | 路由 | 单页任务 |
| --- | --- | --- |
| M1 | `/admin/usertable` | 用户与权限 |
| M2 | `/admin/config` | 站点与注册 |
| M3 | `/translate-all` | 整本翻译 |
| M4 | `/word-detail-batch` | 全文单词详解 |
| M5 | `/llm-tasks` | LLM 任务中心 |
| M6 | `/admin/credits` | 积分治理 |
| M7 | `/admin/mail` | 运营站内信 |
| M8 | `/admin/viewconfig` | UI 配置 |
| M9 | `/admin/dbconfig` | 数据库配置 |
| M10 | `/admin/mailsettings` | 邮件服务器 |
| M11 | `/admin/scheduledtasks` | 计划任务 |
| M12 | `/admin/logfile` | 日志 |
| M13 | `/admin/debug` | 调试 |

## 11. 第二轮实现

### 11.1 L2 导航单一来源

- `cps/ui_ia.py` 新增 `ACCOUNT_L2_GROUPS`、`ADMIN_L2_GROUPS` 与 `l2_nav_groups(domain, path)`。
- 导航元数据同时包含 id、标签、endpoint 和路径匹配规则；active 只从这一份数据计算。
- `partials/l2_nav.html` 只渲染分组纯文字链接，不使用卡片和页内仪表盘。
- 页头标题只显示“账号”或“管理”，不显示内部层级缩写“L2”。
- `jinjia.py` 新增 `l2_nav_groups` filter；模板不复制第二份 A/M 路由表。

### 11.2 账号拆页

- `/me` 只保留资料、OIDC 绑定和语言；移除难度、词汇量测试、主题、伙伴、导出。
- 用户名、邮箱改为 14px 左对齐的资料网格；删除页面底部指向其他 L2 的迁移提示。
- 难度、词测、主题与使用引导迁入 `/reading/settings`；新增独立 `reading-preferences.js`。
- 学习数据导出迁入 `/me/export`，复用原 R230 的 create/tasks/download 接口。
- `/buddy` 增加“打开 AI 伴读”按钮，调用 `window.AICompanion.openChat()`，不复制聊天 DOM。

### 11.3 管理拆页

- 旧 `/admin/view` 由 `admin.admin()` 302 到 M1，保留 Calibre 原生 Back/Cancel endpoint 的兼容。
- 顶栏“管理”直接指向 `/admin/usertable`，不再经过旧仪表盘。
- M4 `/word-detail-batch` 在缺少 `book_id` 时渲染选书说明页，不再返回 400；从书籍详情进入时仍走预览/入队。
- 用户 `/credits` 与 `/admin/credits` 拆为两个模板；新增 `data-credit-mode` 分流加载，
  用户页不渲染任何治理表单，管理页只加载治理数据。

### 11.4 最小侵入

- 继续复用 Calibre 的 Bootstrap 外壳、路由命名和关键 DOM ID；只重组 MagicBook 自有页面。
- 新页面只增加产品层模板/CSS/JS；没有修改 vendored Calibre CSS、基座模型或数据库 schema。
- 旧的顶层 Settings 入口改为最小 Help 菜单，只保留使用引导；L2 入口统一由账号/管理页头承接。

### 11.5 统一账号中心入口

> 「账号 下的用户名和邮箱地址可以了，下边的提示也没问题，但是加一个跳转链接到 account.haoshenqi.top」

- 在 A1 `/me` 的账号说明下方增加 `#me-account-center`，链接到
  `https://account.haoshenqi.top/`，新窗口打开并带 `rel="noopener noreferrer"`。
- 中文文案为「前往统一账号中心」，保持“先解释、再行动”的顺序；不复用
  MagicBook 的“管理”域，避免与站内后台混淆。
- 只修改产品层 `me.html` / `magicbook.css` / 中文 PO+MO，不改 Calibre 登录、
  OIDC issuer、路由或模型。
- 渲染守卫覆盖 DOM ID、目标 URL、新窗口与 `noopener noreferrer`；CDP 实测
  390×844 与 1440×1200 均 `scrollWidth == innerWidth`，链接可见且无溢出。
- 实现 `2de2a538` 已推送并上线；fnOS `build END OK`、app-manager
  `deploy SUCCESS`，容器 `running / healthy`，镜像
  `house.build-sha=2de2a5388d2cf598a2f36a65ada778d7e8f8c29d`、
  `house.code-digest=533d440f819b943e`。

### 11.6 功能地图独立成 L1 文档

> 「把完善好的功能地图写入文档，在 readme 里引用」

- 新增 L1 `docs/product/readme/feature-map.md`，集中维护五域总览、按任务找功能、
  八支完整功能树以及 A1–A7 / M1–M13 页面索引。
- `docs/product/readme/readme.md` 增加「功能地图」主入口，模块手册继续承担各功能的
  使用细节，不复制全图。
- L3 `ui-information-architecture.md` 删除重复功能树，只保留页面归属、权限边界、
  active 与测试要求，并链接 L1 功能地图。
- 长期规则写入 KB：用户视角功能树只维护一份；新增或移动功能时先改功能地图，
  再同步模块手册与实现边界。

### 11.7 README 全册巡检

> 「检查 readme 文件夹，更新里边的文档。然后 merge develop push」

- 逐份检查 `docs/product/readme/` 全部 10 份 Markdown：系统索引、书库、阅读器、
  词汇、学习、伙伴、积分、管理和功能地图，并新增账号手册 `account.md`。
- `account.md` 用 A1–A7 索引账号任务，统一说明统一账号中心、OIDC、注销只结束本站
  SSO 会话以及管理入口仅管理员可见。
- 产品 README 补齐账号域入口，按仓库实况纠正 L2 覆盖数量，并删除面向用户的
  “账号/管理 L2”称谓；页头内部层级缩写不再出现在使用手册。
- MagicLens 统一表述为“扩展优先接管、阅读器内置能力兜底”，删除硬编码且已过期的
  扩展版本号，修正“阅读器划词已下线”和全文单词详解发起权限两处历史漂移。
- 失效后端指针改为现行路径；moon-well `mail/requirements.md` 明确标为语义参考，
  不把尚未建立的 mail L2 冒充接口契约。
- 本巡检只改文档，不改代码、模板、CSS、路由、模型或 Schema。目录内 10 份 Markdown
  共 72 条相对链接全部有效；`test_account_admin_ia_r251.py` 与
  `test_home_nav_shell.py` 定向回归 23 passed / 0 failed / 2 warnings。

## 12. 第二轮验证

定向回归：

```text
tests/test_account_admin_ia_r251.py
tests/test_home_nav_shell.py
tests/test_buddy_page.py
tests/test_credit_card.py
tests/test_credit_consume.py
tests/test_credit_page_r245.py
tests/test_admin_mail_r250.py
tests/test_mail_ui_r243.py
tests/test_me_preferences.py
tests/test_nav_settings_dropdown.py
tests/test_reader_theme_sync.py

150 passed / 0 failed / 2 warnings
```

新增 R251 守卫覆盖：

- A1–A7 / M1–M13 数量、唯一 id、每条 owned route 恰好一个 active；
- `/me` 不再含难度/词测/主题/导出，`/reading/settings` 与 `/me/export` 各自承接；
- `/buddy` 只有一个“打开 AI 伴读”，脚本复用共享 `AICompanion.openChat`；
- 用户积分与管理员积分治理 DOM/权限物理分离；
- 顶栏管理直达 M1，旧 `/admin/view` 仍 302；
- M4 无 `book_id` 有有效落地页。

正式发布态全量回归：

```text
pytest tests/ -q
1206 passed / 0 failed / 4 warnings
```

其中收尾修复了 JS i18n 清单仍引用已删除 `me.js`、旧 Help 下拉导航断言、
`Help` 缺少中文词条三条契约链；新增 `reading-preferences.js` 的 `mbT()` 词条
全部进入种子、PO/MO。验收后的细节修正又去掉了“账号/管理”后的 L2 小字，
将 A1 用户名/邮箱改为 14px 左对齐，并删除 `/me` 底部迁移提示；
账号说明下方增加统一账号中心入口；中文 PO/MO 同步为「前往统一账号中心」。

上线验证：

- 第二轮初始实现 `af55130797714946cce4270b7e64e2cbdd4ee1c7` 已上线；
- 验收修正 `3a75a695577da1e4d945b5bb90e0bc7a20d9f08a` 已推送 `origin/develop`；
- fnOS `build END OK (3a75a695577da1e4d945b5bb90e0bc7a20d9f08a)`；
- app-manager `deploy SUCCESS`，容器 `running / healthy`；
- `house.build-sha=3a75a695577da1e4d945b5bb90e0bc7a20d9f08a`，
  `house.code-digest=dc464e7a3c38db3a`；
- 生产 `/login` 200；匿名 `/me`、`/buddy`、`/credits`、`/admin/credits`、
  `/translate-all`、`/word-detail-batch`、`/llm-tasks` 均按预期 302 到登录页。

真实 Chromium：

- 抓取时必须用 CDP `Emulation.setDeviceMetricsOverride` 设置 390×844；直接给
  Headless Chrome `--window-size=390` 仍可能得到 500px 布局视口，再把 PNG 裁成 390px，
  会制造“横向溢出 + 第四项底栏消失”的假缺陷。
- 设备模拟下 `/me`、`/reading/settings`、`/me/export`、`/buddy`、`/credits` 的
  `document.documentElement.scrollWidth == 390`，移动底栏四项都在视口内。
- 1440px 下账号 L2 单行/自然换行，页面内容保持左侧阅读宽度，不横向滚动。

## 13. 文档四问（第二轮）

- 能力变了：L1 `readme/{readme,library,reading,vocabulary,companion,credit,admin,learning}.md`
  同步账号/管理拆页、伙伴入口、主题与积分页归属。
- 契约变了：`credit/interface.md` 更新用户积分页与 `/admin/credits` 的页面/DOM 边界；
  HTTP 代理端点本身不变。
- 实现/边界变了：L1 新增独立 `product/readme/feature-map.md`（功能地图单一来源）；
  L3 `product/library/features/ui-information-architecture.md` 保留 A/M 路由表、伙伴关系与
  用户/管理治理分离并引用该地图；`reading/features/reader-theme-sync.md`、
  `credit/features/page-layout.md`、`credit/features/credit-card.md` 同步迁页。
- 本次怎么实现：本 LLD、AC、需求基线与 `REQUIREMENTS.md`；长期原则追加到
  `docs/kb/instructions/coding/ui-information-architecture.md`。
