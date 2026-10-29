# LLD — R251 MagicBook UI 信息架构与导航分组

> 状态：**已上线待验收**（2026-10-29；实现 `1910fce7`，文档与发布提交 `bfea06fb`；定向 12 passed / 0 failed，正式发布态全量 1188 passed / 0 failed）
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

- `48327926..bfea06fb` 已推送 `origin/develop`；
- fnOS `build END OK (bfea06fbf1075ac55dc11d578a7bf46130e0703e)`；
- app-manager `deploy SUCCESS`，容器 `running / healthy`；
- `house.build-sha=bfea06fbf1075ac55dc11d578a7bf46130e0703e`，
  `house.code-digest=78d752f6d510768a`；
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
