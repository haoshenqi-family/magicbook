# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R01-R31.md`：R1–R31（2026-08-14 ～ 2026-08-31）
- `response-archive/response-R32-R49.md`：R32–R49（2026-09-03 ～ 2026-09-17）
- `response-archive/response-R50.md`：R50（2026-09-18）
- `response-archive/response-R51-R70.md`：R51–R70（2026-09-18 ～ 2026-09-21）
- `response-archive/response-R70-R80.md`：R70–R80（2026-09-22 ～ 2026-09-28；含 R70/R71 历史重复条与 R74 补写条，见文件头说明）
- `response-archive/response-R81-R101.md`：R81–R101（2026-09-27 ～ 2026-09-30；含 R88/R90/R98 补记与重复编号，原样搬移）

---

## 2026-09-30（导航栏「设置 Settings」下拉框）

### R102（magicbook 自有设置入口收纳为下拉框 + 双语标签）

- **需求**：magicbook（非 calibre-web 部分）的设置入口平铺放不下，改下拉框跳转；页面双语，默认中文。
- **现状盘点**：导航栏平铺项 = 阅读设置（theme 0）/ 成就 / 积分；theme 1 三项塞在头像下拉；整本翻译 /translate-all（admin）无任何入口；另有指向已退役 /ai/admin（R98 起 410）的死链 AI 按钮。admin 账号 locale=en 且 magicbook 词条未入 po——纯 Babel 方案对实际用户永远显示英文，故标签不走 i18n。
- **实现**（`cps/templates/layout.html`）：新增主题无关的「设置 Settings」Bootstrap 3 下拉框（id=top_mb_settings，登录可见）：阅读设置/成就/积分 + admin 分隔线后整本翻译（与路由 @admin_required 一致）；移除 theme 0 三处平铺项、theme 1 头像下拉三处重复项与死链 AI 按钮。标签「中文 + 英文辅助（small.text-muted）」双写，任何 locale 下中文可见。
- **顺带清理**：删除孤儿模板 `cps/templates/ai_admin.html`（无任何代码渲染、引用已退役端点，R98 退役漏网件）。
- **测试**：新增 `tests/test_nav_settings_dropdown.py` 5 项——admin 全入口、双语标签（圈定在下拉块内，防 <title> 假信心）、平铺项/死链不回流 + id 唯一性、普通用户无 admin 项、匿名不渲染；全量 221 passed。Code Review（交叉 agent）：无 P0，3 个 P1（孤儿模板/非 admin 用例/断言圈定）均已修复。
- **交付**：推 develop；CI 处于 disabled_manually，生产生效需 fnOS 手动构建链。工作区另有 login.html 未提交改动（R100 会话遗留，与本条无关，未纳入提交）。
- **AC**：无独立 ac/ 目录，本条与单测即验收记录。

### 总结

- **requests.md**：占号 R102。
- **response.md**：本条；保留窗口 R92–R102（未到 10 整倍数，无归档动作）。本次提交顺带携带 R101 会话留在工作区的 response.md 未提交记录（补登）。
- **冲突记录**：无。

## 2026-09-30（登录页邀请制注册入口）

### R103（Authentik 邀请注册链接放登录页 + R100 遗留补登）

- **需求**：把 Authentik 邀请制注册链接放到 magicbook 首页，跟登录入口放一起。
- **现状确认**：生产 `/` 对游客 302 → `/login`（匿名浏览关闭），游客首页即登录页；同源会话已在 Authentik（2025.10.2）侧建好 `invitation-enrollment` 邀请注册流程与 30 天期邀请（见 authentik-invite-enrollment 记忆）。另发现工作区有 R100 会话遗留的 login.html 未提交改动（移除右下角重复 Authentik 链接 + endif 错位修正），生产实际仍渲染两个按钮——单独补登为 `5c92e125`。
- **实现**：`cps/web.py` `render_login` 从环境变量 `AUTHENTIK_ENROLLMENT_INVITE_URL` 读取邀请链接注入 `authentik_invite_url`；`cps/templates/login.html` Authentik 分支在登录按钮下渲染「注册账号 Sign up (invite)」按钮（target=_blank 不打断登录页 + 一行邀请制说明，标签中英双写不走 Babel，与 R102 约定一致）；未配置变量时不渲染，邀请轮换只改 `.env` 重启即可。
- **测试**：新增 `tests/test_login_invite_link.py` 3 项（配置时渲染且指向配置链接、未配置不渲染、本地登录分支忽略该变量）；`tests/conftest.py` 建_app 阶段补注册 oidc 蓝图（修复用例内注册报 "setup method can no longer be called"——会话级 app 处理过请求后 Flask 拒绝 register_blueprint；config 开关仍由用例 monkeypatch 控制，不影响其他用例）。全量 224 passed。
- **交付与部署**：`247ba434` 推 develop。push 后 fnOS webhook-builder 链**自动**构建并经 app-manager 触发 fnOS 部署 SUCCESS（15:43，build END OK (247ba434)）——此前认知"CI 停用后需手动构建"已过时：GitHub 仓库 webhook → fnOS webhook_listener → build-magicbook.sh 链路在自动工作。随后 fnOS `/app/magicbook/.env` 追加 `AUTHENTIK_ENROLLMENT_INVITE_URL`（备份 .env.bak-20260930-invite）+ `./deploy.sh` 重建容器使变量生效。
- **生产验证**：`/login` 渲染 1 个「Log in with Authentik」（R100 去重同步生效）+ 1 个 `#authentik_invite_signup`，href 与邀请链接一致；`/` 仍 302 → `/login`；浏览器截图确认排版正常。
- **AC**：无独立 ac/ 目录，本条与单测即验收记录。
- **对 requests.md/response.md 的总结**：requests.md 占号 R103；response.md 本条；保留窗口 R93–R103（未到 10 整倍数，无归档动作）。
- **冲突记录**：无。R100 遗留改动与本条同文件（login.html），已拆分为两个独立提交（5c92e125 / 247ba434），历史可区分。

## 2026-09-30（登录页文案简化）

### R108（删除邀请制提示句 + Authentik 长句简化）

- **需求**：①删「注册采用邀请制，请使用管理员发放的邀请链接 / Registration is invite-only...」提示句；②"Sign in with your Authentik account"→"Sign in"；③"Log in with Authentik"→"Log in"。
- **实现**（`cps/templates/login.html`，Authentik OIDC 分支）：提示段整块删除；muted 提示与主按钮改为 "Sign in" / "Log in" 纯文本（不走 Babel——原 msgid 本就不在 po，行为不变、文案确定）。邀请注册按钮（注册账号 Sign up (invite)）与 URL 注入逻辑不动。
- **测试**：`tests/test_login_invite_link.py` 旧断言同步 + 新增 `test_login_copy_simplified` 锁定简化后文案、旧长句与提示句不得回流；4 项全过，全量 240 passed。
- **交付**：推 develop；生产生效需 fnOS 手动构建链。
- **对 requests.md/response.md 的总结**：requests.md 占号 R108（首次误写 103 与并行会话冲突，按纪律续编，条目内已注明）；response.md 本条；保留窗口 R98–R108（未到 10 整倍数，无归档动作）。
- **冲突记录**：占号时 R103 已被并行会话（邀请注册入口）占用，本条续编 R108；并行会话在 admin.py/main.py/conftest.py 等文件有未提交改动（halo-book-connector），本条未触碰。

## 2026-09-30（并行会话产出代提交推送）

### R110（代提交：R107 halo-book-connector + R109 onboarding）

- **需求**：把工作区并行会话的未提交改动提交并推送。
- **盘点与归属**：工作区改动属两个已完成实现的功能——① R107 halo-book-connector（并行会话在 R106 咨询/R107 LLD 基础上实施了内部导入 API）：`cps/book_import.py`（245 行）+ `main.py`/`admin.py` 接线 + `tests/test_book_import.py`（204 行）+ `tools/connector/`（Halo 侧连接器服务，含 compose/Dockerfile）+ `docs/feat/halo-book-connector/design/`；② R109 前端 onboarding 引导：`onboarding.js/css` + `onboarding_mount.html` + layout/read 模板挂载 + `tests/test_onboarding_tour.py`（177 行）+ `docs/feat/onboarding-tour/design/`。
- **验证**：全量 **251 passed**（224 存量 + 并行会话新增 27 项）；关键安全点确认——`main.py` 按 `BOOK_IMPORT_KEY` fail-closed 注册导入 API（生产未配置该变量 → 路由不注册、不暴露），`admin.py` 将其加入免 db_configuration 劫持白名单保持 JSON 错误契约，`conftest.py` 仅测试环境无条件注册蓝图。
- **交付**：拆两个代码提交 `0806da06`（R107）/ `44cd4721`（R109）+ 本记录提交，单次推送 develop；push 后 fnOS webhook-builder 链自动构建部署（进度见 /app/codelib/logs/magicbook.log）。
- **对 requests.md/response.md 的总结**：requests.md 占号 R110；response.md 本条；保留窗口 R94–R110（未到 10 整倍数，无归档动作）。
- **冲突记录**：无。R109 会话的 response 未写（会话已结束），本条仅代提交与验证，功能层面的回应留待原会话补登或按需追记；R108（登录页文案简化）仍占号未实施。

## 2026-10-02（R109 引导模式功能层回应补登 + 浏览器验收发现 4 个缺陷并修复）

### R109（前端引导模式 onboarding：实现、实跑验收与缺陷修复）

- **需求**：做一个前端引导模式，带新用户在真实界面上学会用 magicbook。形态经确认取「纯 spotlight 逐步导览」（蒙层挖洞 + 气泡指向真实控件），状态持久化取「服务端 `User.view_settings`」（跨设备权威，localStorage 只作断点续览），覆盖「浏览/搜索/书架/下载」+「阅读器 + AI 伴读」+「引导读 R104 指南书 #89」，触发为「首次自动邀请 + 常驻手动入口」，邀请卡可在任意页面出现，指南书按 id 89 硬引用。
- **实现（零 Python 改动、零迁移）**：新增 `cps/static/js/onboarding.js`（引擎 + 两段步骤表：主段 13 步 / 阅读器段 8 步）、`cps/static/css/onboarding.css`、`cps/templates/onboarding_mount.html`（状态种子 include），`layout.html` 挂入口 `#top_onboarding`（设置下拉内，双语标签）+ include，`read.html` 挂 include + 常驻「?」。写入复用既有 `POST /ajax/view`（`web.py:229`），读取直接在模板里取 `current_user.view_settings`；匿名访客只走 localStorage（`ub.Anonymous.set_view_property` 写的是 `flask_session`，模板读的是共享行，服务端那条写入对匿名无意义）。
- **验收方式**：本地临时实例（`docs/temp/run_onboarding_check.py`，CSRF 保持开启）+ 真实浏览器逐帧量 `getBoundingClientRect()`。已验：邀请卡四按钮、主段逐步高亮几何、锚点缺失自动跳过（3→12→13）、`点我试试 Go` 的点击捕获与 `window.open`、跨段 handoff 落 `{segment:"reader",step:"toc"}`、完成/跳过写回 `view_settings`（`POST /ajax/view` 200 且落库）、刷新不再邀请、手动入口无视「以后再说」可重开、ESC 只收起不记 seen、`later` 按段隔离、匿名不发写请求、阅读器段 8 步（AI 悬浮球只在 `onb-step-ai` 一步放行）、指南链接探测降级。
- **实跑发现并修复 4 个静态检查看不见的缺陷**（详见设计文档 §11）：① 气泡按目标原始 rect 定位，指向高于视口的侧栏时 `top:-181` 飞出屏幕 → 改为按 `drawMask()` 与视口求交后的「洞」定位 + `top` 夹取 + 超高元素顶对齐滚动；② 居中「导览完成」卡从未真正显示过——jQuery 3 的 `.show()` 对未入树元素不生效而 `#onb-bubble` 默认 `display:none`（窄屏同路径同受影响）→ 先 append 再显式 `css("display","block")`；③ `onb-step-*` 换步不清，残留会让 AI 悬浮球在后续步骤继续盖住卡片 → 抽出 `clearStepClass()`；④ scroll 不冒泡而 caliBlur 主题下真正滚动容器是 `.col-sm-10`（`overflow:auto`），洞与目标脱钩（实测容器滚 260px 后目标到 1638、洞仍钉在 258）→ 改捕获阶段监听。四条各补源码级回归断言防「顺手简化」改回。
- **测试**：`tests/test_onboarding_tour.py` 16 项（挂载唯一性、三种 `view_settings` 形态渲染、角色显隐、`/ajax/view` 写入通道真实落库、锚点存在性、上述 4 条回归）；全量 **255 passed**。
- **未验（诚实边界）**：本机无 calibre `metadata.db`，`/`、`/book/<id>`、`/read/...` 三类页面 500，真实书库下的详情页/阅读器步骤未实地走过（用同页注入阅读器锚点驱动真实引擎替代，控件 id 一致性由模板测试锁定）；窄屏 <768 未在真实小视口截图。CSRF 端到端未被测试覆盖（`conftest.py` 关用了 `WTF_CSRF_ENABLED`），但已在本地实例开着 CSRF 实跑过 200。
- **对 requests.md/response.md 的总结**：requests.md 占号 R109（本条为其功能层回应，R110 已代提交快照、留待补登）；response.md 本条。
- **冲突记录**：**R110 提交并推送的 `44cd4721` 是本功能修复前的快照**——上面 4 个缺陷（含「完成卡不可见」）以及 code review 阶段的修复（`<link>` 从 body 移入 head、AI 浮层由仅禁指针改为按步放行、ESC 不再误记 seen 等）都还在工作区未提交，`git status` 显示 7 个文件 modified（+302/−99）。若 develop/生产要拿到修好的版本，需要另行提交推送（未擅自操作）。另：本文件保留窗口已超 10 个 request（现存 R90/R94–R110），R94–R97 及重复的 R90 条目按规则应原样归档至 `response-archive/`，本次未做（涉及搬运并行会话的记录，留待确认）。

## 2026-10-02（R111 阅读器导览视觉重做：降噪微调，保留挖洞）

### R111（「图书内的导览太丑了」——阅读器段 spotlight 视觉）

- **需求**：阅读器内导览观感差。经逐项确认，痛点四项全中：① 蒙层太重（整屏 `rgba(0,0,0,.62)` 盖住正在读的书页）② 挖洞的 2px `#4285f4` 蓝描边土气、像截图标注工具 ③ 360px 纯白圆角卡 + 投影是 Bootstrap 味、与阅读器排版两套语言 ④ 文字太多（中英两段正文 + 四个按钮，一步读一屏字）。方向选定「降噪微调，保留挖洞」：形态不动，只压数值、换语汇。
- **实现**（`onboarding.css` 重写 + `onboarding.js` 几何）：
  - **蒙层分级**：主段 `.38`、阅读器段 `.18`、居中卡 `.45/.30`；深色主题下「黑压黑」无对比，改极淡白纱 `.10/.08`。
  - **环去描边**：`#onb-ring` 不再 `border`，改 `inset 0 0 0 1px` 细内描边 + 内影 + `0 0 10px 4px` 外柔影，边缘色走 `--onb-ring-edge/--onb-ring-glow` 变量。
  - **卡片对齐阅读器语汇**：照 `.reading-translation-popover`（`radius 6px`、`0 4px 18px rgba(0,0,0,.22)`、accent `#4a90d9`），宽度 300px / 阅读器段 258px / 居中卡 320px，字号 13px。**根因之一**：`read.html` 不引 bootstrap，旧 `.btn .btn-primary` 在阅读器里渲染成浏览器原生灰按钮——按钮改为自带 `.onb-btn`。
  - **亮区与环分离**：`drawMask(protect, ring)`；阅读器段 `protectFor()` 取目标所在**整条工具带**（`closest("#titlebar, #sidebar, .read-footer")`）留亮，书页只吃薄纱；主段仍按目标外扩 12px。`visualRect()` 去掉 `.arrow` 的 160/80px 透明内边距热区（只在元素自身无背景/无背景图时内缩，否则按钮会被高亮成「几个字」）。
  - **深浅色卡**：`body.onb-chrome-dark` 只在阅读器段出现，按 `#main` 实际计算底色算亮度（`0.299R+0.587G+0.114B<140`）而非抄主题对照表——5 套主题加可任取颜色的 `customTheme`，查表必漏。作用域类 `onb-seg-main/onb-seg-reader/onb-chrome-dark` 在 `teardown()` 一并清理。
- **验收方式**：本机无 calibre 书库、`/read/...` 起不来，故建 gitignored 静态夹具 `docs/temp/reader_fixture.html`（按 `read.html:186-276` 1:1 复刻 DOM，引真实 CSS/JS，`?tour=1&at=N&dark=1&debug=1` 驱动并把 target/side/ring/bubble 的 rect 打进 `<pre id="dbg">`）+ 无头 Chrome 逐帧截图（`--window-size=1440,987 --virtual-time-budget=25000`，profile 每次唯一且串行）+ browser-use `evaluate_script` 读几何量。实跑（视口 831×741）：`#sidebar`=(0,0,300,741) 为亮区、环=(2,9,26,28) 只勾 18×20 的 `#show-Toc`、气泡 258×116 贴洞右侧。夹具暴露并修掉 3 个静态检查看不见的缺陷：环漏 `position:fixed` 画在 (0,0)、箭头热区圈出大块空白、深色主题无对比。
- **测试**：新增 `tests/test_onboarding_reader_visual.py` 15 项源码级回归锁（蒙层浓度单调、深色白纱、**级联顺序按规则字节位置**、环无硬描边且 fixed/pointer-events、卡片宽度相对关系、配色走变量、`read.html` 无 bootstrap 且按钮自给自足、工具带亮区、`visualRect` 内缩条件、作用域类设置与清理、亮度探测、常驻「?」重算次序、气泡 z-index 高于蒙层、蒙层容器放行点击/四边拦截）。全量 **278 passed**（含并行 R112 的 i18n 契约用例）。
- **交叉 Code Review（独立 agent）**：无 P0；3 条 P1 全部修掉——① `body.onb-chrome-dark #onb-mask.onb-dim` 与 `body.onb-seg-reader #onb-mask.onb-dim` 特异度相同、原先写在前面被静默覆盖（深色主题的居中卡仍是黑压黑，白纱设计永不生效），已调序并加**按规则字节位置**的断言（做过变异测试：换回顺序即红）；② `teardown()` 摘掉 `onb-chrome-dark` 后，常驻「?」因 `showReaderHelp()` 提前返回不再重算配色，导览结束那刻从暗色卡跳回白按钮 → 重算移到提前返回之前；③ R112 交叉产生的死选择器 `#onb-invite .onb-invite-title small` 连同 `.onb-title-en` 删除。另修一处对比度回退：深色主题环的外柔影原为黑色（黑底等于没有），改 `rgba(255,255,255,.16)` 淡白光晕，截图 `/tmp/r_d2_{band,paging}.png` 复核目标明显「亮起来」且浅色主题不受影响。未采纳的两条（换主题时配色要到下一步才跟上、次要按钮 opacity .62 对比度 4.4:1 略低于 AA）记入设计稿 §12.7 遗留。
- **文档**：设计稿新增 §12（痛点表、两段作用域、protect/ring 分离、夹具与实跑数据、与 R112 的边界、未验项）——`docs/feat/onboarding-tour/design/onboarding-tour.md`。
- **未验（诚实边界）**：真实书库下的端到端观感；主段（layout 页）在真实页面的截图——其 R111 差异只有蒙层 `.38` 与 `expand(rect,12)` 两个数值，已由源码断言覆盖，观感待用户线上走一遍确认。
- **对 requests.md/response.md 的总结**：requests.md 占号 R111（该条目已在会话中先行登记）；response.md 本条；按归档规则（R110 已完成却未归档，本次补做）把 R102 之前的 21 条回应**原样**搬移至 `response-archive/response-R81-R101.md`，保留窗口现为 R102–R111。
- **冲突记录**：**与并行 R112（语言模块）会话同文件并发写入**。R111 期间 `onboarding.js / layout.html / read.html / login.html / messages.po(.mo) / tests/test_onboarding_tour.py` 被 R112 会话同时改写，并新增 `cps/templates/i18n_seed.html`；Edit 工具两次提示 "file changed since your last read"。处置：① R111 的视觉逻辑（`setSegmentScope/applyChromePalette/expand/protectFor/visualRect/paintMask/drawMask(protect,ring)`、`.onb-btn`）在合并后的工作区**全部存活**，未被覆盖；② 原计划由 R111 落的「正文只留中文」由 R112 的 `mbT()` 取词方案实现得更彻底（中英双写行整体删除），R111 相应删除了已失效的 `#onb-bubble .onb-title-en` 死规则；③ 为避免争用同一测试文件，R111 的 15 项断言**另起新文件** `tests/test_onboarding_reader_visual.py`，未改写 R112 在写的 `tests/test_onboarding_tour.py`（该文件里「中文为主 + 英文辅助双写」的旧断言由 R112 改为走 gettext 单语，属其职责范围）。两拨改动目前都还在工作区未提交，提交前需两会话产出都稳定。

## 2026-10-02（语言模块修复：按 locale 单语切换 + JS 层 i18n 通道）

### R112（「语言模块还是有问题。很多没有双语设置，很多直接把双语显示出来了，而不是根据选择的语言切换」）

- **需求**：R102 的双语方案落地后仍有两类问题——① 很多控件中英并排硬显示，不随账号语言切换；② 很多 magicbook 自有文案中文用户看到的仍是英文。形态经两项确认：msgid 用**英文** + `zh_Hans_CN` po 出译文（与上游 Calibre-Web 约定一致，`pybabel extract` 的 jinja2 抽取器可扫），三个 User Story 全做。
- **根因拆分（三个独立成因，不是一件事）**：① R102 的「中文 + `<small>English</small>`」双写**刻意绕过 Babel**，locale 再怎么设都是两行字；② magicbook 自有 `_()` msgid 从未进过 `zh_Hans_CN` po，`_()` 只能回退 msgid（英文）；③ `epub.js` / `ai_chat.js` / `onboarding.js` 是静态 JS，**根本没有本地化通道**，阅读器里所有提示恒英文。
- **US1 模板层**：`layout.html` 设置下拉（阅读设置/成就/积分/使用引导/整本翻译）与 `login.html`（`Sign in` / `Log in` / `Sign up`）的双写全部改 `{{ _('...') }}`，入口 id 一个不改（DOM 契约）；magicbook 自有 msgid 补入 po。
- **US2 JS 通道 + 引导**：新增 `cps/templates/i18n_seed.html`——模板里 `{% set mb_i18n = {"Skip": _("Skip"), ...} %}` 渲染成 `window.MB_I18N`，配 `window.mbT(id)` 取词，消费侧统一 `var mbT = window.mbT || function (id) { return id; };` 降级；`onboarding.js` 两段步骤表（13 + 8 步）改英文 msgid 并删掉 `.onb-title-en` 英文副标题行。挂载次序是硬约束：种子必须早于 `epub.js`（顶层作用域取词），`readtxt.html` / `readpdf.html` 也补了 include（它们经 `ai_chat_panel.html` 加载 `ai_chat.js`，漏挂即静默回退）。
- **US3 阅读器文案收编**：`epub.js` 55 处、`ai_chat.js` 21 处中文字面量走 `mbT()`，含整本翻译台账、段落批注、TTS、生词本、会话与记忆面板、学情画像；带变量的句子重构成占位符式 `mbT('Whole-book translation completed: {d}/{t}').replace('{d}', …)`。
- **msgid 复用陷阱（实测）**：`Edit` / `Delete` 在上游 po 已译作「编辑书籍」「删除数据」，记忆面板复用会显示错误文案 → 改用独立 msgid `Edit memory` / `Delete memory`；`'Delete this memory?\n'` 这种把换行写进 msgid 的形态与运行时字符串不逐字符相等（po 查不到即静默英文）→ msgid 去掉换行，`\n` 在 `mbT()` 之外拼接。
- **测试**：新增 `tests/test_i18n_seed_contract.py` 4 条源码级契约（① 种子 key 与 `_()` 实参逐字符相同；② 三个 JS 的 `mbT('字面量')` 都在种子里；③ 每个种子 msgid 在 po 有非空译文；④ `onboarding.js` 步骤表 title/body 都在种子里——动态取词正则抓不到，尾点缺陷正出在这一类），并用变异测试确认四条**各自**能复现对应缺陷；渲染层在 `test_onboarding_tour.py`（种子只注入一次、en 取回 msgid、zh 取回中文并遍历全部 144 词条非空）、`test_nav_settings_dropdown.py`（en 无中文回流 / zh 无双写回流）、`test_login_invite_link.py`。全量 **275 passed**。
- **交叉 Code Review 与事故**：审查无 P0，三条 P1 全部处理——(1) 种子 key 带尾点而 `_()` 实参不带（zh 用户静默拿英文）；(2) 学习画像 3 个前缀 msgid（`Difficulty: ` / `Topics: ` / `Frequent words: `）用了 `mbT()` 却没进种子与 po，属本轮引入的本地化倒退；(3) `i18n_seed.html` 仍是 untracked 文件（提交时必须 `git add`）。P2 里修了有实际后果的一条：`String.replace` 的第二参对 `$&`/`$1` 做特殊展开，而生词文本、伴读角色名、会话名三处占位符填的正是用户可控文本（实测 `'删除会话「{t}」'.replace('{t}', '$& 测试')` 会把占位符吞掉），已改回调形式并 `node --check` 通过；其余 P2（种子内联体积、CSS `content` 里 `Tr` 徽标的脆弱性、`esc()` 不转义属性引号）记入设计稿「未采纳项与遗留」，不在本轮扩大改动面。**处置 (2) 时出过一次事故**：`write_po` 参数名写错抛异常，而目标 `.po` 已被 `open(..., "wb")` 截断为 0 字节。恢复姿势是从 `git show HEAD:` 取 base po + 用已编译的 `.mo`（1083 条译文，恰为收编后的最终态）回灌，再补 3 条新词条；事后逐条比对确认 **base 876 条 msgid 零丢失、零译文倒退、新增 211 条**。教训与脚本一并留在设计稿 §8（改 po 要写临时文件再原子替换，译文字典同时留副本）。
- **文档**：`docs/feat/language-i18n/design/language-i18n.md`（三成因对照表、种子通道四条设计约束、msgid 复用坑、四条契约、改动清单、未采纳项、事故记录）+ `docs/feat/language-i18n/ac/language-i18n-ac.md`（US1 6 项 / US2 6 项 / US3 6 项 + 回归 4 项，逐条对齐测试）。
- **未验（诚实边界）**：本机无 calibre 书库，`/`、`/book/<id>`、`/read/...` 起不来，zh 账号在真实阅读器里的中文渲染未做浏览器实跑（由 `test_i18n_seed_renders_chinese_for_zh_user` 的渲染层断言 + 契约测试覆盖）；`epub.js` 里注释与注释掉的代码仍留中文（不参与渲染，故意不动）。种子内联约 9KB/页，词条再膨胀时改独立 JSON + fetch。
- **对 requests.md/response.md 的总结**：requests.md 占号 R112（会话开始时登记）；response.md 本条；保留窗口 R102–R112（未到 10 整倍数，无归档动作）。
- **冲突记录**：① **本条推翻 R102 的一条决策**——R102 因「admin 账号 locale=en、magicbook 词条未入 po，纯 Babel 对实际用户永远英文」选了双写；本轮把词条补进 po 并让用户改用 zh_Hans_CN locale 后，双写失去存在理由，按 R112 需求删除。R102 条目文字保留不改（记录不回改）。② 与并行 R111 会话同文件并发写入（`onboarding.js` / `layout.html` / `read.html` / `messages.po(.mo)` / `tests/test_onboarding_tour.py`），Edit 工具多次提示 "file changed since your last read"；本条改动（步骤表 msgid 化、种子注入）与 R111 的视觉几何（`drawMask(protect, ring)` / `.onb-btn` / 作用域类）在合并后的工作区互不覆盖，全量 275 passed 含 R111 的 12 项视觉断言。③ 两拨改动均未提交；`cps/templates/i18n_seed.html`、`tests/test_i18n_seed_contract.py` 是新增文件，提交时需显式 `git add`（未擅自提交/推送，线上生效还需 fnOS 构建链）。
