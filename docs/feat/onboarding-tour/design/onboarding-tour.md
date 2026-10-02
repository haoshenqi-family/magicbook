# Magicbook 前端引导模式（Onboarding Tour）— LLD 设计稿

> 对应需求：`requests.md` R109 — 为 magicbook 做一个前端引导模式，引导用户学习使用这个系统。
> 状态：设计草案，待用户确认后进入编码。

## 1. 目标与形态

让用户在**真实界面上**学会用 magicbook 的主流程：找到书 → 看懂详情 → 加入书架 → 下载/在线阅读 → 用 AI 伴读 → 找到设置与成就积分入口。

采纳的形态决策（与用户确认）：

| 维度 | 决策 |
| --- | --- |
| 交互形态 | 纯 spotlight 逐步导览（蒙层挖孔 + 气泡指向真实控件），不做任务清单 |
| 状态持久化 | 服务端 `User.view_settings`（跨设备/换浏览器仍生效），前端 `localStorage` 只做「当前进度」断点续览 |
| 覆盖范围 | 首页区（浏览/搜索/书架/下载）＋ 阅读器内 ＋ AI 伴读 ＋ 收尾指向指南书 #89 |
| 触发时机 | 未看过引导的账号登录后，首页出现非阻塞邀请卡；「设置」下拉常驻「使用引导」手动入口 |

## 2. 核心结论：零 Python 改动

这是本设计最重要的约束收益，避免与并行会话（R107 Halo 连接器正在改 `cps/main.py`、`cps/admin.py`、`cps.web.py`、`tests/conftest.py`）产生文件冲突。

1. **写入状态复用现有端点**：`POST /ajax/view`（`cps/web.py:229-240`）
   遍历请求 JSON 并调用 `current_user.set_view_property(element, param, value)`（`cps/ub.py:218-230`）。
   引导直接发 `{"onboarding": {"seen": true}}`，落进已有的 `User.view_settings` JSON 列（`cps/ub.py:260`），无需迁移、无需新路由。

2. **读取初始状态走 Jinja**：`current_user` 是 Flask-Login 注入的 Jinja 全局，模板里已在用（`layout.html:43`、`:77`）。因此可在模板内安全取值，无需新增 context processor：
   ```jinja
   {% set ob_state = ((current_user.view_settings or {}).get('onboarding') or {}) %}
   ```
   `or {}` 链同时兜住三种情况：`view_settings` 为 `None`（列空）、`current_user` 为 `AnonymousUserMixin`（属性 Undefined，falsy）、`onboarding` 键不存在。

3. **前端交付物全是新增文件**：`cps/static/js/onboarding.js` + `cps/static/css/onboarding.css`；改动仅限模板挂载点。

## 3. 状态模型

| 状态 | 存储位置 | 键 | 说明 |
| --- | --- | --- | --- |
| 是否已看过/已跳过引导（权威） | 服务端 `User.view_settings` | `onboarding.seen` (bool) | 决定是否自动弹邀请卡、以及「使用引导」是否显示为「重新开始」 |
| 当前导览进度（断点续览） | `localStorage` | `calibre.onboarding.progress` = `{step, updatedAt}` | 跨页面跳转后恢复；跟随既有命名风格 `calibre.<域>.<子项>`（见 `js/reading/epub.js:667`、`js/ai_chat.js:28`） |
| 邀请卡「以后再说」 | `localStorage` | `calibre.onboarding.later` = `1` | 本次浏览器不再自动提示，但不清服务端 `seen`，手动入口仍可开启 |

**匿名访客必须只落 localStorage。** `admin.py:107` 的 before_request 允许 `config_anonbrowse`，此时 `current_user` 是 `ub.Anonymous`，其 `view_settings` 来自 `ROLE_ANONYMOUS` 那一条**共享**用户记录（`cps/ub.py:297-313`）。给它写 `onboarding.seen` 会污染所有匿名访客，且是单行竞态。所以前端按 `data-onboarding-anonymous` 判定，匿名单元跳过服务端写入。

## 4. 挂载点

| 位置 | 文件 | 改动 |
| --- | --- | --- |
| 全站（浏览/详情/书架/设置页均 `{% extends "layout.html" %}`） | `cps/templates/layout.html` | `<head>` 内加 `onboarding.css`；`</body>` 前、`main.js` 之后加 `onboarding.js`；`<body>` 上加 `data-onboarding-seen` / `data-onboarding-anonymous` |
| 阅读器（不继承 layout 的独立 HTML） | `cps/templates/read.html`、`readpdf.html` | 逐页 include css+js（先例：`read.html:531` 的 `{% include 'ai_chat_panel.html' %}`） |
| 手动入口 | `cps/templates/layout.html:103-111` 的 `#top_mb_settings` 下拉内 | 新增 `<li><a id="top_onboarding" href="#"> 使用引导 <small class="text-muted">Onboarding Tour</small></a></li>` |

v1 不覆盖：`readtxt.html`、`readcbr.html`、`listenmp3.html`、`basic_layout.html`（simple 主题）、OPDS。这些页面结构差异大或走独立 layout，收益低；后续按同一 include 姿势扩展。

## 5. Spotlight 引擎（`onboarding.js`）

IIFE + 原生 DOM，与 `achievements.js`/`credits.js` 的 magicbook 自有惯例一致（不依赖 jQuery 选择器缓存，不引入第三方 tour 库 —— 项目 `js/libs/` 无 intro.js 类资产，新增第三方依赖不值得）。

- **蒙层**：1 个 `position: fixed` 容器 + 4 块阴影矩形拼出中间「洞」，比 SVG mask 简单且不需跟随目标尺寸重算 path。目标用 `getBoundingClientRect()`，先 `scrollIntoView({block:'center'})` 再取 rect，监听 `resize`/`scroll` 重绘。
- **气泡**：绝对定位于洞的下方/上方/侧方（按剩余视口自动选位），含 步骤标题、正文、`3 / 20` 进度、上一步 / 跳过 / 下一步。
- **点击拦截**：蒙层吃掉所有点击，只有气泡按钮和「跳转类步骤」的真实目标元素放行（给目标临时加 `pointer-events: auto` + 高亮环）。
- **目标缺失容错**：某步骤的 selector 在当前页找不到（角色门控、主题差异、书库为空）→ 自动跳过该步继续，不卡死在空白气泡。
- **窄屏（<768px）**：不挖孔，蒙层整体半透明 + 气泡居中；导航类步骤只提供「前往」链接。

## 6. 步骤表（v1，共 20 步）

双语遵循 R102 惯例：**中文为主 + 英文辅助双写，不走 Babel**（`layout.html:95-97` 已注释说明原因）。每步文案两段，同气泡内渲染。

**A. 首页 / 浏览**（`/`，锚点见 `layout.html`、`index.html`）

| # | selector | 讲什么 |
| --- | --- | --- |
| 1 | `#scnd-nav` | 左侧「浏览」分类：最新/热门/评分/已读/未读/随机… |
| 2 | `#query` | 顶部搜索框，库内即时检索 |
| 3 | `#advanced_search` | 高级搜索：按作者/系列/出版社/语言多维过滤 |
| 4 | `#books` | 书墙；点封面看详情，右键/context menu 有快捷操作 |
| 5 | `#list-button` | 网格 ↔ 列表视图切换、排序按钮 |
| 6 | `.book.session` (first) | 跳转类：点它进详情页（导览在新页面自动续） |

**B. 书籍详情**（`/book/<id>`，锚点见 `detail.html`）

| # | selector | 讲什么 |
| --- | --- | --- |
| 7 | `#detailcover` | 封面与元数据区：作者/系列/标签/评分/出版社 |
| 8 | `#btnGroupDrop1` | 下载：EPUB/PDF/TXT 等格式（按账号下载权限） |
| 9 | `#shelf-actions` | 加入书架 / 移出书架（书架是自选书单） |
| 10 | `#read-in-browser` | 跳转类：在浏览器里打开阅读器 |
| 11 | `#have_read_cb` | 「已读完」标记，驱动统计与成就 |

**C. 阅读器 + AI 伴读**（`/read/<id>/`，锚点见 `read.html`、`ai_chat_panel.html`）

| # | selector | 讲什么 |
| --- | --- | --- |
| 12 | `#show-Toc` | 目录 / 书签面板 |
| 13 | `#prev` | 左右翻页（键盘方向键同样可用） |
| 14 | `#setting` | 阅读设置：主题、字号、字体、版式、TTS 朗读 |
| 15 | `#immersive-translate` | 沉浸式翻译与划词查词/释义 |
| 16 | `#bookmark` | 添加书签，进度自动记忆 |
| 17 | `#fullscreen` | 全屏沉浸阅读 |
| 18 | `#ai-companion-fab` | **AI 伴读抽屉**：就当前书提问、多会话、记忆面板 |

**D. 收尾**

| # | selector | 讲什么 |
| --- | --- | --- |
| 19 | `#top_mb_settings` | 「设置」下拉：阅读设置 / 成就 / 积分 |
| 20 | 自定义卡片（无 selector，居中卡） | 指向《Magicbook User Guide》书 #89 作为延伸阅读 + 「完成」按钮 |

完成 / 跳过 / 关闭 → `POST /ajax/view {"onboarding":{"seen":true}}`（登录账号）并清 `calibre.onboarding.progress`。

## 7. 自动触发时序

```
页面加载 → onboarding.js 读 body[data-onboarding-*]
  ├─ progress 存在且未过期（同一 session 内、<24h）→ 续览：直接渲染 progress.step
  └─ 否则
       ├─ seen=0 且 非匿名/匿名可写 localStorage 且 later=0 且 当前页是首页
       │    → 渲染非阻塞邀请卡（开始引导 / 以后再说 / 不再提示）
       │      ·「开始引导」→ 进步骤 1，写 progress
       │      ·「以后再说」→ 写 later=1
       │      ·「不再提示」→ 写 seen=true
       └─ seen=1 → 什么都不做（「设置 → 使用引导」仍可手动开启；点击时重置 progress 从第 1 步开始）
```

邀请卡**不阻塞**操作，位置右下，避免遮挡书墙；这与 R100/R108 的登录页「不要多余按钮/文案」取向一致 —— 引导是可选服务，不是关卡。

## 8. 测试计划（`tests/test_onboarding_tour.py`）

沿用 `tests/test_nav_settings_dropdown.py` 的姿势：以 `/reading/settings` 作为最稳的 layout 载体页（无需 calibre 库）。模板/契约测试，不做浏览器 e2e：

1. layout 挂载：`onboarding.css`、`onboarding.js` 在设置页出现且各只出现一次。
2. 状态注入：登录账号 `view_settings={}` 时 `data-onboarding-seen="0"`；预置 `{"onboarding":{"seen":true}}` 后为 `"1"`。
3. `view_settings` 为 `NULL` / 匿名访问 `/login` 时页面 200，不抛 UndefinedError（守住第 3 节的 Jinja 兜底链）。
4. 手动入口：`#top_onboarding` 在 `#top_mb_settings` 块内、且双语标签齐备；匿名不渲染（下拉框本身对匿名隐藏）。
5. 阅读器挂载：`read.html`、`readpdf.html` 模板源码含 include（模板文件级断言，避免构造完整书库）。
6. 持久化契约：登录态 `POST /ajax/view {"onboarding":{"seen":true}}` 返回 200 且 `current_user.view_settings['onboarding']['seen'] is True` —— 锁住我们依赖的既有端点不被上游改动破坏。
7. 匿名不写服务端：匿名（开启 anonbrowse）POST 后，`ROLE_ANONYMOUS` 用户行的 `view_settings` 不变（守住第 3 节的污染风险；若前端无法自证，则断言该端点对该场景的行为并在测试注释说明由前端 gating 保证）。

交付标准：`python3 -m pytest tests/ -q` 全绿 + 本地 `python cps.py` 起服务后，用浏览器走完 20 步（含跨页续览、窄屏、跳过/不再提示三条分支）。

## 9. 已知取舍

- **书 #89 用常量 id**：`onboarding.js` 里 `GUIDE_BOOK_ID = 89`。硬编码 id 跨环境不稳（书库重导即变），但当前生产固定；解析失败时该步降级为普通文案，不显示链接。
- **整本翻译 / 上传 / 任务页不进引导**：受 `role_admin` / `role_upload` 门控（`detail.html:80`、`layout.html:77`），普通账号看不见锚点，靠第 5 节的「目标缺失自动跳过」兜住，若管理员跑引导会自然跳过这些步——v1 不为管理员单独编排章节。
- **不引入 intro.js**：约 300 行自研引擎覆盖需求，新增第三方前端资产对单页静态挂载不划算。

## 10. 实现偏差记录（编码时确认，R109）

设计稿与落地代码的差异，均以实际模板结构为准：

1. **阅读器段只挂 `read.html`（EPUB）**。原计划同挂 `readpdf.html`，实测该页**没有 jQuery**
   （只有 `pdf.js`/`viewer.js` 两个 module 脚本），且控件锚点不同（`#previous` 而非
   `#show-Toc`/`#setting`/`#bookmark`），挂上去只会得到一段全部自动跳过的空导览。
   顺带发现：`readpdf.html` include 了 `ai_chat_panel.html`，而 `ai_chat.js` 是
   `(function($){...})(jQuery)` —— PDF 阅读器里的 AI 伴读大概率本来就跑不起来（既有问题，
   不在本次范围，待单独立项）。
2. **步骤 4/5 选择器改写**：`#books` 只在浏览页存在（首页是 `page='discover'` 分支，用
   `#books_rand`），`#list-button` 只在 `grid.html`。故「书墙」指向 `.book.session`、
   「排序」指向 `.filterheader`，两者在真实首页/浏览页都能命中或安全跳过。
3. **跳转类步骤在洞上盖一层点击捕获**（`.onb-catch`）。原设计是「放行原生点击」，
   但封面链接是 `data-toggle="modal" data-target="#bookDetailsModal"`，Bootstrap modal 的
   z-index 约 1050，会被蒙层压暗；`#readbtn` 又是 `target="_blank"`。改为捕获后统一由
   `gotoTarget()` 决定 `location.href` / `window.open`，行为可预期。
4. **详情页新增「在浏览器里读」一步**（`#readbtn, #read-in-browser`）：受
   `role_viewer() and role_admin()` 门控（`detail.html:80`），普通账号自动跳过、
   管理员能看到，之后在阅读器页由第二段导览接手。
5. **邀请卡可在任意 layout 页面出现**（按用户确认，不限首页）。
6. **指南书链接降级**：`#89` 收尾卡里的链接渲染后用一次 GET 探测，非 200 就摘掉，不留死链。
7. **挂载 include 自带 `csrf_token` 隐藏域**。原因不只是引导本身：`layout.html` 里原本只有
   上传表单带 token，普通用户在无上传权限的页面上 `main.js` 的 `$.ajaxSetup` 取到空值，
   写 `/ajax/view`（视图/排序偏好）会静默 400。补上之后这条通道对所有人都成立。
8. **导览期间冻结 `#ai-companion-fab`**：它用 `2147483646` 这种顶级 z-index，蒙层压不住，
   不禁用指针事件就能被绕过（见 `onboarding.css` 的 `body.onboarding-active` 规则）。

