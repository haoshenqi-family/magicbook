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
| 手动入口 | `cps/templates/layout.html` 的 `#top_mb_settings` 下拉内 | `<li><a id="top_onboarding" href="#">{{ _('Onboarding Tour') }}</a></li>`（R112 起走 gettext 单语，不再是「使用引导 + small 英文」双写） |

v1 不覆盖：`readtxt.html`、`readcbr.html`、`listenmp3.html`、`basic_layout.html`（simple 主题）、OPDS。这些页面结构差异大或走独立 layout，收益低；后续按同一 include 姿势扩展。

## 5. Spotlight 引擎（`onboarding.js`）

IIFE + 原生 DOM，与 `achievements.js`/`credits.js` 的 magicbook 自有惯例一致（不依赖 jQuery 选择器缓存，不引入第三方 tour 库 —— 项目 `js/libs/` 无 intro.js 类资产，新增第三方依赖不值得）。

- **蒙层**：1 个 `position: fixed` 容器 + 4 块阴影矩形拼出中间「洞」，比 SVG mask 简单且不需跟随目标尺寸重算 path。目标用 `getBoundingClientRect()`，先 `scrollIntoView({block:'center'})` 再取 rect，监听 `resize`/`scroll` 重绘。
- **气泡**：绝对定位于洞的下方/上方/侧方（按剩余视口自动选位），含 步骤标题、正文、`3 / 20` 进度、上一步 / 跳过 / 下一步。
- **点击拦截**：蒙层吃掉所有点击，只有气泡按钮和「跳转类步骤」的真实目标元素放行（给目标临时加 `pointer-events: auto` + 高亮环）。
- **目标缺失容错**：某步骤的 selector 在当前页找不到（角色门控、主题差异、书库为空）→ 自动跳过该步继续，不卡死在空白气泡。
- **窄屏（<768px）**：不挖孔，蒙层整体半透明 + 气泡居中；导航类步骤只提供「前往」链接。

## 6. 步骤表（v1，共 20 步）

文案（R112 起）：步骤表存**英文 msgid**，气泡渲染前经 `mbT()` 查 `window.MB_I18N` 种子（`cps/templates/i18n_seed.html`），按账号 `locale` 出对应语言，缺词条回退英文。初版（R109）沿用 R102 的「中文为主 + 英文辅助双写」，实测在阅读器里一步要读中英两屏字，且与账号语言设置无关，已由 R112 统一收进 gettext 链路——机制细节见 `docs/feat/language-i18n/design/language-i18n.md`。

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
4. 手动入口：`#top_onboarding` 在 `#top_mb_settings` 块内、标签单语（R112：en 账号出 `Onboarding Tour` 且无中文回流，zh 账号出「使用引导」）；匿名不渲染（下拉框本身对匿名隐藏）。
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


## 11. 浏览器实跑发现的缺陷（R109 验收，均已修复）

在本地临时实例（`docs/temp/run_onboarding_check.py`，CSRF 保持开启）用真实浏览器逐帧量了
`getBoundingClientRect()`，暴露 4 个静态检查看不见的问题：

1. **气泡定位基准错了**：`position()` 拿的是目标原始 rect。第一步指向侧栏 `#scnd-nav`
   （高 1135px > 视口 741px），其 `top` 是 -181，走到「右侧」分支时 `top = rect.top`
   直接把气泡推到屏幕外（`top:-181`）。改为以 `drawMask()` 与视口求交后的「洞」为基准，
   并对 `top` 兜一次视口夹取；同时超高元素改为顶对齐滚动（`block:"start"`），
   否则 `scrollIntoView({block:"center"})` 会把它的上半截推出视口。
2. **完成卡从未显示过**：居中路径写的是 `$("body").append(centered.show())`。jQuery 3 的
   `.show()` 对**未插入文档**的元素不生效（`isHiddenWithinTree` 要在树内判定），而
   `#onb-bubble` 默认 `display:none`，于是「导览完成」卡一直静静挂在 DOM 里。
   窄屏（<768）走同一条路径，同样受影响。改为先 append 再显式 `css("display","block")`。
3. **`onb-step-*` 类换步不清**：`render()` 每步只 `addClass`，旧类残留。CSS 靠
   `body.onboarding-active.onb-step-ai #ai-companion-fab` 放行那个 z-index 高于蒙层的悬浮球，
   残留会让它在后续步骤上继续盖住导览卡片。抽出 `clearStepClass()`，加新类前先摘旧类。
4. **滚动时高亮洞与目标脱钩**：监听原本挂在 `$(window).on("scroll")`，但 scroll 事件不冒泡，
   而 caliBlur 主题下真正的滚动容器是 `.col-sm-10`（`overflow:auto`）。实测容器滚 260px 后
   目标已到 `top:1638`、洞仍钉在 `top:258`。改为捕获阶段监听
   `window.addEventListener("scroll", onViewportEvent, true)`。

四条都补了源码级回归断言（`test_centered_card_is_displayed_after_append`、
`test_bubble_is_positioned_against_the_hole`、`test_step_class_is_replaced_not_accumulated`、
`test_scroll_listener_uses_capture_phase`），防止后续「顺手简化」把它改回去。

### 实跑覆盖与未覆盖

已验（真实浏览器 + 真实 CSRF）：邀请卡渲染与四个按钮、13 步主段的逐步高亮几何、锚点缺失
时自动跳过（3→12→13）、`点我试试 Go` 的点击捕获与 `window.open`、跨段 handoff 落
`{segment:"reader", step:"toc"}`、完成/跳过写回 `User.view_settings`（`POST /ajax/view` 200
且落库）、刷新后不再邀请、常驻手动入口可无视「以后再说」重开、ESC 只收起不记 seen、
`later` 按段隔离、匿名访客只写 localStorage 不发请求、阅读器段 8 步（含 AI 悬浮球只在
`onb-step-ai` 一步放行）、指南书链接探测降级（本地 `/book/89` 500 → 链接被摘）。

未验：真实 calibre 书库下的 `/`、`/book/<id>`、`/read/...` 三个页面（本机没有 `metadata.db`，
这些路由 500）——阅读器段是用「同页注入阅读器锚点」驱动真实引擎跑的，控件 id 与
`read.html` 的一致性由 `test_reader_step_anchors_exist_in_template` 锁；窄屏（<768）的
居中路径与完成卡共用同一分支，已随缺陷 2 一并修复但未在真实小视口下截图。

## 12. R111：阅读器段视觉重做（用户反馈「图书内的导览太丑了」）

> 对应需求：`requests.md` R111。方向经用户选定为「降噪微调，保留挖洞」——形态不动
> （仍是 spotlight 逐步导览），只把四个具体痛点按数值压下去。

### 12.1 痛点与对策

| # | 痛点（用户原话逐项确认） | 对策 | 落点 |
| --- | --- | --- | --- |
| 1 | 蒙层太重：整屏 `rgba(0,0,0,.62)` 盖住正在读的书页 | 主段降到 `.38`；阅读器段 `.18`；居中/完成卡 `.45 / .30`。深色主题下黑压黑无对比，改极淡白纱 `.10 / .08` | `onboarding.css` 的 `.onb-side` / `.onb-dim` 四组规则 |
| 2 | 挖洞的 2px `#4285f4` 蓝描边像截图标注工具 | 环不再描边：`inset 0 0 0 1px` 细内描边 + `inset 0 2px 5px` 内影 + `0 0 10px 4px` 外柔影，颜色走 `--onb-ring-edge/--onb-ring-glow` 变量 | `#onb-mask .onb-ring` |
| 3 | 360px 纯白圆角卡 + 投影是 Bootstrap 味，与阅读器排版两套语言 | 卡片对齐阅读器里已有的 `.reading-translation-popover` 语汇（`radius 6px`、`0 4px 18px rgba(0,0,0,.22)`、accent `#4a90d9`），宽度 300px（阅读器段 258px、居中卡 320px），字号 13px/1.5 | `#onb-bubble` / `.onb-card` |
| 4 | 文字太多：中英两段正文 + 四个按钮，一步读一屏字 | 英文正文行删掉；卡片只留标题＋一段正文＋按钮。按钮自带 `.onb-btn` 样式（`read.html` 不引 bootstrap，原来的 `.btn` 在阅读器里渲染成浏览器原生灰按钮，是「丑」的直接来源之一） | `buildBubble()` + `.onb-btn` |

### 12.2 两段作用域与深浅色卡

- `body.onb-seg-main` / `body.onb-seg-reader`（`setSegmentScope()`）区分两段，蒙层浓度、
  卡片宽度、亮区规则全部挂在作用域类上，互不影响；`teardown()` 连同 `onb-chrome-dark`
  一起清掉，避免类残留让书库页沿用阅读器的轻蒙层。
- `body.onb-chrome-dark` **只在阅读器段**出现（`applyChromePalette()`）：书库页的气泡本来就
  浮在蒙层上，不存在压住正文的问题。判定按 `#main` 的实际计算底色算亮度
  （`0.299R+0.587G+0.114B < 140`）而不是再抄一份主题对照表——`read.html` 有 5 套主题加
  可任取颜色的 `customTheme`，查表必漏。`#main` 取到透明值时退到 `body`，仍透明按亮底处理。

### 12.3 亮区（protect）与环（ring）分离

`drawMask(protect, ring)` 用 4 块 `.onb-side` 围出「亮区」，环只勾目标本身（外扩 4px）。
两者不再等同，是这一轮几何上的关键变化：

- 主段：`protect = expand(rect, 12)`，亮区≈目标。
- 阅读器段：`protectFor()` 取目标所在的**整条工具带**（`closest("#titlebar, #sidebar, .read-footer")`），
  整条留亮——用户能看到目标旁边的兄弟控件，书页只吃一层薄纱。目标不在工具带里
  （翻页箭头、AI 悬浮球）退化为 `expand(rect, 18)`。
- `visualRect()` 去掉「不可见的点击热区」：`.arrow` 带 160px 上下、80px 左右内边距
  （`main.css:115-141`），照 border-box 挖洞会圈出一大块空白，环看起来像画错了。
  **只在元素自身没有背景色/背景图时**才按 padding 内缩——按钮的底色铺在自己的 padding 上，
  内缩会把「控件」高亮成「控件里的几个字」。
- 环必须 `position: fixed`（本轮重写 CSS 时漏过一次，环画在 `0,0` 64×64）且
  `pointer-events: none`（否则盖住自己圈住的那个可点控件）。两条都进了回归锁。

### 12.4 验证方式：静态夹具 + 无头截图

本机没有 calibre 书库，`/read/...` 真实页面起不来，因此用 `docs/temp/reader_fixture.html`
（gitignored，`.gitignore:51`）按 `read.html:186-276` 1:1 复刻静态 DOM（`#sidebar/#panels/#show-Toc/
#titlebar/#prev/#viewer/#next/.read-footer/#ai-companion-fab`），引真实 `main.css/reader.css/
onboarding.css/onboarding.js`，用 `?tour=1&at=N&dark=1&debug=1` 驱动到第 N 步并把 target/side/ring/bubble
的 rect 打进 `<pre id="dbg">`。截图 `chrome --headless=new --window-size=1440,987
--virtual-time-budget=25000 --screenshot`；几何量用 browser-use 的 `evaluate_script` 读 `#dbg`。

实跑数据（`?tour=1&at=0`，视口 831×741）：`#sidebar` = `(0,0,300,741)` 即亮区，
环 = `(2,9,26,28)` 只勾 `#show-Toc`（18×20），气泡 258×116 贴在洞右侧 `x=314`。
翻页一步的亮区由 `#next` 原始 `(709,178,101×393)` 内缩为约 `60×115`，与截图一致。

三个只有实跑才暴露的缺陷（环画在 0,0、箭头热区圈出大块空白、深色主题无对比）均已修复，
截图为证：`/tmp/r_f_{toc,paging,ai}.png`、`/tmp/r_dark2.png`。

### 12.5 与 R112（语言模块）的边界

R111 只动视觉（`onboarding.css` 全部 + `onboarding.js` 的 `setSegmentScope/applyChromePalette/
expand/protectFor/visualRect/paintMask/drawMask` 与 `.onb-btn` 按钮标记）；文案的取词链路
（`mbT()` / `MB_I18N` 种子 / po）属 R112。两拨改动已在同一工作区合并，`tests/test_onboarding_tour.py`
里「中文为主 + 英文辅助双写」的断言由 R112 改写为走 gettext 单语，R111 的 4 项回归锁未受影响。

### 12.6 回归锁与未验项

新增 `tests/test_onboarding_reader_visual.py`（15 项，源码级）：蒙层浓度单调关系、深色白纱、
**级联顺序（规则字节位置）**、环无硬描边且 fixed/pointer-events、卡片宽度相对关系、配色走变量、
`read.html` 不引 bootstrap 且按钮自给自足、工具带亮区、`visualRect` 内缩条件、作用域类的设置与清理、
亮度探测、常驻「?」的重算次序、气泡 z-index 高于蒙层、蒙层容器放行点击而四边拦截。
全量单测 278 passed（含并行 R112 的 i18n 契约用例）。

未验：真实 calibre 书库下的端到端观感（本机无 `metadata.db`）；主段（layout 页）在真实页面上的
截图——其 R111 差异只有蒙层 `.38` 与亮区 `expand(rect,12)` 两个数值，已由源码级断言覆盖，
但观感仍需用户在线上走一遍确认。

### 12.7 交叉 review 吸收（独立 agent 视角）

review 抓到 3 个 P1 + 1 处对比度回退，全部已修并补断言：

1. **级联顺序**：`body.onb-chrome-dark #onb-mask.onb-dim` 与 `body.onb-seg-reader #onb-mask.onb-dim`
   特异度相同（`body.x #id.y`），原先写在前面 → 深色主题的居中卡仍是黑压黑 `.30`，白纱永不生效。
   已把 chrome-dark 那组移到段规则之后并就地注释「必须排在后面」；
   `test_dark_gauze_rule_wins_the_cascade_tie` 用**规则字节位置**而不是数值来锁（已做变异测试：
   把顺序换回来该断言即红）。这是源码级断言最容易漏的一类 bug——数值都对，生效的不是它。
2. **常驻「?」配色回跳**：`teardown()` 摘掉 `onb-chrome-dark`，而 `showReaderHelp()` 在
   `if ($("#onb-help").length) return` 之后才 `applyChromePalette()` → 导览结束后那个按钮从暗色卡
   跳回白底浮在深色主题上。重算移到提前返回之前，`test_help_button_palette_is_recomputed_before_early_return` 锁顺序。
3. **R112 交叉死代码**：`#onb-invite .onb-invite-title small`（双写 `<small>` 已被 `mbT()` 取代）
   与 `#onb-bubble .onb-title-en` 一并删除。
4. **深色环的指引太弱**：`--onb-ring-glow` 原为 `rgba(0,0,0,.42)`，黑底上等于没有，目标只剩 1px
   白内描边。深色主题改为 `rgba(255,255,255,.16)` 淡白光晕（落在洞外蒙层上），
   截图 `/tmp/r_d2_{band,paging}.png` 对比确认：翻页箭头一步的目标明显「亮起来」，浅色主题不受影响（变量按主题分覆盖）。

未采纳（记入遗留）：`applyChromePalette()` 只在 `render/showInvite/showReaderHelp` 触发，用户在
「主题」一步现场换主题时，卡片配色要到下一步才跟上——修法要么监听 `#themes` 变更、要么给 `#main`
挂 `style` 属性的 MutationObserver，属新增监听面，本轮不扩大改动；`.onb-btn` 次要按钮 `opacity:.62`
在两种卡面上的对比度约 4.4:1，略低于 WCAG AA 的 4.5:1，与 R109 之前一致，未在本轮调整。
