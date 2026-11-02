# 对话回应归档：R102–R110

> 自 response.md 轮转搬入（R120 触发，120%10==0），原样未改。R110 条目内含 R107/R109 并行会话代提交记录。

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

