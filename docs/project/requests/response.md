# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R01-R31.md`：R1–R31（2026-08-14 ～ 2026-08-31）
- `response-archive/response-R159.md`：R159 语音输入静音检测（2026-10-14 R169 轮转，窗口转入 R160 起）
- `response-archive/response-R160-R164.md`：R160 麦克风设备选择器 + 同节嵌套的 R164 worktree 纪律修订（2026-10-14 R170 写入触发轮转搬移，父级日期标题随节一并搬移）
- `response-archive/response-R161-R162.md`：R161 公网入口超时排查（Tailscale 直连黑洞）+ R162 两本《傲慢与偏见》版本对比（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起）
- `response-archive/response-R32-R49.md`：R32–R49（2026-09-03 ～ 2026-09-17）
- `response-archive/response-R50.md`：R50（2026-09-18）
- `response-archive/response-R51-R70.md`：R51–R70（2026-09-18 ～ 2026-09-21）
- `response-archive/response-R70-R80.md`：R70–R80（2026-09-22 ～ 2026-09-28；含 R70/R71 历史重复条与 R74 补写条，见文件头说明）
- `response-archive/response-R188.md`：R188（2026-10-16）
- `response-archive/response-R81-R101.md`：R81–R101（2026-09-27 ～ 2026-09-30；含 R88/R90/R98 补记与重复编号，原样搬移）
- `response-archive/response-R102-R110.md`：R102–R110（2026-09-30 ～ 2026-10-01；R110 条目含 R107/R109 代提交，R120 触发轮转搬入）
- `response-archive/response-R111-R119.md`：R111–R119（2026-10-02 ～ 2026-10-05；2026-10-08 R129 补账搬移）
- `response-archive/response-R120-R125.md`：R120–R125（2026-10-06 ～ 2026-10-07；R135 写入触发搬移，含 R134 登记的窗口欠账补账）
- `response-archive/response-R126-R131.md`：R126、R127、R128、R129、R131（2026-10-07 ～ 2026-10-08；2026-10-09 R141 写入触发轮转搬移，清掉 R134 登记的窗口欠账）
- `response-archive/response-R132-R133.md`：R132、R133（2026-10-08；2026-10-10 R143 写入触发轮转搬移）
- `response-archive/response-R134.md`：R134（2026-10-08；2026-10-10 R144 写入触发轮转搬移，其父级日期标题随节一并搬移）
- `response-archive/response-R143.md`：R143（2026-10-10；2026-10-11 R157 写入触发轮转搬移）
- `response-archive/response-R144-R153.md`：R144、R145、R147（含嵌套 R146）、R151、R152、R153（2026-10-10 ～ 2026-10-11；2026-10-12 R161 写入触发轮转搬移，清并行欠账）
- `response-archive/response-R154.md`：R154（2026-10-11；2026-10-12 R162 写入触发轮转搬移）
- `response-archive/response-R165-R173.md`：R165、R166、R167、R168、R169、R170、R172、R173（2026-10-12 ～ 2026-10-14；2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起）
- `response-archive/response-R174-R177.md`：R174、R176、R177（2026-10-15；2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起）
- `response-archive/response-R175.md`：R175（2026-10-15；2026-10-16 R188 写入触发轮转搬移，窗口转入 R178 起）
- `response-archive/response-R178.md`：R178 moon-well 防腐层迁出 web.py（B1，架构评审波 2）（2026-10-15；2026-10-16 R189 写入触发轮转搬移）
- `response-archive/response-R179.md`：R179 架构评审 B2 尝试（撤销回基线，留存重做清单）（2026-10-15；2026-10-19 R130 写入触发轮转搬移）
- `response-archive/response-R130.md`：原文件标 R130 节、正文实为 R190 回应（LLM 队列监控面板四区块）（2026-10-23 R209 写入触发轮转搬移，原样搬移不改写）
- `response-archive/response-R180.md`：R180 B2 前置小修两项（2026-10-21 R190 写入触发轮转搬移）
- `response-archive/response-R130.md`：R130 LLM 队列监控面板（承接 moon-well R118 契约、扩展 R126 /llm-tasks），2026-10-21 R191 写入触发轮转
- `response-archive/response-R181.md`：R181 架构评审波 3 · B2 小步重做完成：web.py 蓝图分域拆分（2026-10-21 台账合并时轮转搬移）
- `response-archive/response-R182.md`：R182 架构评审波 4 · B7：i18n 种子与 JS 清单生成化（2026-10-21 台账合并时轮转搬移）
- `response-archive/response-R185.md`：R185 架构评审文档修正批 DF1–DF5（2026-10-22 R207 写入触发轮转搬移）
- `response-archive/response-R191.md`：R191 写作批改 503 复发（代理预算小于后端 LLM 预算）——2026-10-23 R210 写入触发轮转搬移
- `response-archive/response-R183.md`：R183 B4 epub.js 分域（批次 1–7 七节，78 行）——2026-10-23 R211 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R194.md`：R194 写作批改 SSE 进度流（2026-10-23 R214 写入触发轮转搬移，窗口转入 R195 起）
- `response-archive/response-R195-R202.md`：R195–R202 博客导入链与 TED 导入链缺陷盘点 + 修复——2026-10-23 R216 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R203.md`：R203 跨模块别名漏声明致 4 个段落按钮失效——2026-10-23 R216 写入触发轮转搬移（与 R214 轮转叠加后续搬），原样搬移不改写
- `response-archive/response-R204.md`：R204 写作批改 SSE 真机无进度（WSGI 缓冲）——2026-10-23 R216 第三次 merge 后窗口达 11 续搬，原样搬移不改写
- `response-archive/response-R205.md`：R205 每日学习「单词编故事」Hub 第八张卡（2026-10-23 R212 写入触发轮转搬移）
- `response-archive/response-R206-R207.md`：R206 伙伴系统前端 + R207 伙伴验收三连与 CSP 拦图修复——2026-10-24 R213-C 写入触发轮转搬移（搬移前窗口已 11 节），原样搬移不改写
- `response-archive/response-R208.md`：R208 每日学习 banner 小功能管理（齿轮抽屉 + 勾选过滤 + 引导卡）——2026-10-24 R213-C 合入 `origin/develop` 后窗口达 11 节（与 R214-C 验收缺陷节并行追加）触发续搬，原样搬移不改写
- `response-archive/response-R209.md`：R209 积分内测活动 + 充值倍率机制（充值页代理与前端）——2026-10-24 R213-C 与 R217 在 develop 合流后窗口达 11 节触发轮转搬移，原样搬移不改写
- `response-archive/response-R210.md`：R210 伙伴图片未生效的定性与 MinIO 入口切换的 CSP 侧（源清单收敛单点、过渡双源）——2026-10-24 R213-C / R217 / R221 再次合流后窗口达 11 节触发续搬，原样搬移不改写
- `response-archive/response-R211.md`：R211 OIDC 自助注册默认授予管理员权限（P0 缺陷修复）——2026-10-24 R222 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R214.md`：R214 书籍详情子项 A（阅读入口解禁 + 元数据修正 + 视觉分层，含 B 合流记录）——2026-10-24 R223 写入触发轮转搬移，原样搬移不改写
---

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移） · [response-R155-R156.md](response-archive/response-R155-R156.md)（2026-10-13 R166 写入触发轮转搬移，含同日同编号「细筛」那条） · [response-R157.md](response-archive/response-R157.md)（2026-10-13 R166 分支 merge origin/develop 后窗口仍达 11，续搬最旧一节） · [response-R156-mic.md](response-archive/response-R156-mic.md) · [response-R158.md](response-archive/response-R158.md)（2026-10-13 R168 写入触发轮转搬移）（2026-10-13 R167 写入触发轮转搬移；与 response-R155-R156.md 里的同编号「细筛」条目不同事） · [response-R160-R164.md](response-archive/response-R160-R164.md)（2026-10-14 R172 写入触发轮转搬移，窗口转入 R161 起） · [response-R161-R162.md](response-archive/response-R161-R162.md)（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起） · [response-R165-R173.md](response-archive/response-R165-R173.md)（2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起） · [response-R174-R177.md](response-archive/response-R174-R177.md)（2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起） · [response-R175.md](response-archive/response-R175.md)（2026-10-16 R188 写入触发轮转搬移）

## 2026-10-23（R216：引导收敛 + /me 偏好页 + 难度入口前置 + 成就锁态 + 伙伴文案 + IP 风险登记）

### R216（承接 moon-well R208；用户：「阅读 pingcode MB-15。讨论一下怎么修改」→「没问题，确认默认方案，请开始执行」）

- **任务来源**：PingCode 用户故事 MB-15（`X3D_PASH`）/ Ship MAGICBOOK-223，需求台账 R216；来源＝首访体验报告 §六/§七（截图 `e1-learning.png`–`e4-buddy.png`）；关联 R109（引导三段式）、R208（账号级偏好范式）。跨仓同源 **moon-well R208**（存储与契约主责；本功能原占 R207，2026-10-23 让号，见「编号」条）。
- **① 引导收敛**：三处弹窗（主站/阅读器/伙伴页）合成**一套文案、只在主站段自动出现一次**。状态从「浏览器级 localStorage + 每段 view_settings」上收到 moon-well `user_ui_settings.onboarding_seen`；邀请卡只留「开始引导 + ×」，删掉「以后再说 / 不再提示」第三态，ESC 与 × 同义；`seen=false` 但旧 `view_settings.onboarding` 任一段已读时静默回填、不重弹。
- **② `/me` 偏好页**：新建 `me.html`（账号只读块 + 语言表单 + 难度面板 `#difficulty` + 5 个内置主题原生 radio + 伙伴只读卡）。**不再复用 `user_edit.html`/`change_profile`**——旧函数是全量覆盖语义，删掉 Kindle 与 20+ 勾选后缺省字段会把 `random_books` / `sidebar_view` / `locale` 一起重置；改走 `POST /me/preferences` **只写 `locale` 与 `default_language`**。管理员编辑用户仍用 `user_edit.html`，其 `div#user_submit` 改真 `<button type="submit">` 并删掉 `main.js` 的 click 转发，键盘可达。
- **③ 难度入口前置**：首页书墙上方 include `difficulty_entry.html`（可复用 partial，R213 `/home` 直接拿），值由 `difficulty_entry.js` 异步取 `/ajax/reading-settings`，显示「3 - CET4 (default)」；**取不到只显示「点此设置」，绝不猜档位**；深链 `/me#difficulty`（阅读设置页同步加 `id="difficulty"`）。
- **④ 成就占位**：灰块根因是展示层不是缺图标——`.ach-card.locked{opacity:.62}` + `.ach-badge{background:#b8b8b8 !important}`。改为「虚线卡 + 保留 tier 底色 + 徽章右下角锁标」，锁标带 `title`/`aria-label`。
- **⑤ 伙伴文案**：`/buddy` 首段改为「伙伴是 AI 阅读按钮上的那张脸，只改外观，不改变 AI 的英语老师角色」；锁定态按 `unlockType` 给准确文案（成就解锁 / 积分兑换 / 未开放），不再一律「Coming soon」。
- **⑥ IP 风险登记（零代码改动）**：新建 L3 `docs/product/companion/features/buddy-ip-risk.md`——9 只伙伴 = `robot`（本站原创）+ **8 只 HP 派生**（neville/ron/hedwig/hermione/dobby/snape/harry/dumbledore），登记权利来源、当前边界（内测可接受、公开注册/宣传/商业化不可）、以及替换点底账：moon-well `BuddyDefinitionService.seedDefs()`、MinIO `buddy/<code>-{full,head}.png` 与上传脚本、`onboarding.js` 硬编码锚点 `#buddy-claim-hedwig` 与「snowy owl/Hedwig」文案（i18n seed + zh PO）、`user_buddy.buddy_code` 迁移（upsert 不删旧行）。给两套方案（A 只换名/图、B 新 code + 迁移）并建议对外发布前走 B；本条不改任何角色数据或图片。
- **契约与代理**：`cps/routes/preferences.py`（新）三条 `@user_login_required` 透传 `GET /ajax/ui-settings`、`POST .../onboarding/close`、`POST .../reader-theme`（超时 8s，401/500/503 原样透传不伪装成「无数据」）；theme 白名单在**代理层**先挡成 400，不让脏值变成上游 500。moon-well 侧 `user_ui_settings` 单行表 + `Result` 显式包装，读请求不懒建行。
- **验收中揪出的真实缺陷（localStorage 串账号）**：无头实测时邀请卡死活不出现，根因不是缓存——`isSeen()` 把账号状态与**浏览器级** `localStorage.seen` 做了 `||`，同一浏览器换账号会互相压制，这正是 R109「每浏览器各弹一次」的原始根因。改为只认 `accountSeen === true`、`closeOnboarding()` 不再写本地 seen，并新增守卫 `test_seen_is_account_only_not_browser_local`（断言源码无 `localSeen`）。
- **主题账号同步的三种时序**：`ui-prefs.js` 在 `read.html` `<head>` 早载（异步，不阻塞阅读器），账号值合法且用户未手选 → 写 `window.__mbReaderTheme` + `localStorage` 镜像 + 广播 `magicbook:reader-theme`；epub.js 初始值按「同步值 → localStorage → lightTheme」，并监听事件补切；`customTheme` 与任何手选都置 `__mbReaderThemePicked`，晚到的账号值不得覆盖用户动作。子路径部署的 base 由脚本自身 `src` 反推。保存失败只在阅读器 toast、`/me` 状态行显示，本机主题不回滚。
- **i18n（含一次自己的漏做）**：改文案时 JS 已换新串、`i18n_seed.html` 仍留旧三条串与「Later / Never show again」，实测才发现种子没跟上；已删旧串、注册新串，`scripts/generate_i18n_seed.py` 重生成清单（26 文件 / 321 msgid，新增 `achievements.js`/`buddy.js`/`me.js`），zh PO 补词条并重编译 `messages.mo`（只动 zh_Hans_CN，其余 locale 的 `.mo` 未被 `pybabel compile -f` 顺手弄脏）。
- **测试**：新增 `tests/test_me_preferences.py`（9）、`tests/test_reader_theme_sync.py`（6），改写 `tests/test_onboarding_tour.py`（账号级通道注册、fail closed、legacy 回填、匿名不请求、邀请卡两动作、ESC）。开发态按仓规只跑本次与受影响模块：merge `origin/develop` 后 **81 passed / 0 failed**（含 R213 的 `test_home_nav_shell` / `test_reading_progress*`）。跨仓 moon-well `mvn test -Dtest='UserUiSettingsServiceTest,UserUiSettingsControllerTest'`（corretto-21.0.9 + `-Djava.version=21`）判据取 surefire XML：**6 + 5 = 11 绿，failures/errors 全 0**（`mvn -q` 会吞汇总，退出码不可信）。**全量未跑**——那是发布闸门的动作。
- **无头真机验收（本机无 Calibre 书库，姿势＝桩上游 + 真 Flask + 无头 Chrome CDP）**：邀请卡按钮实测 `["×","Start Tour"]`，ESC 关闭后服务端 `onboardingSeen=true`、刷新不再弹；`/me` 出 5 个主题 radio、3 个真 `submit` 按钮、难度显示「3 - CET4 (default)」、伙伴卡出名字与「使用中」；主题保存状态「Theme saved」且账号回读 `darkTheme`；难度保存「Saved ✓」；首页入口文本正确、`href=/me#difficulty` 且锚点落点量到（top 156.78）；成就页 4 卡中 3 锁、虚线边 + tier 色保留 + `opacity:1` + 锁标；伙伴页逐字为新文案，锁定标签三种各现；页面无横向溢出。**截图属临时产物未入库**，逐条结论记在此处。
- **合并后复验（同一套桩上游 + 无头 Chrome，21:2x 重跑）**：merge 动了 `index.html`/`read.html`/`epub.js`/`web.py`，因此在新基线上把验收项重跑一遍——邀请卡按钮仍恰为 `["×","Start Tour"]`、ESC 关闭后服务端 `onboardingSeen=true` 且刷新不再弹；`/me` 五面板齐、5 个主题 radio 默认勾中账号值 `sepiaTheme`、3 个真 `submit`、难度回读 `3`、伙伴卡出 `Bit`、旧控件（kindle_mail/kobo/sidebar_view/random_books）**零命中**；主题存成后服务端回读 `darkTheme` 且本机镜像同步；难度保存状态行带 ✓；`/__verify_entry` 显示「3 - CET4 (default)」且 `href=/me#difficulty`；伙伴页英文文案逐字、锁定标签分成「完成成就后解锁 / 用积分兑换解锁 / 未开放」三类；成就 4 卡 3 锁、`border-style: dashed`、`opacity: 1`、银档底色 `rgb(124,136,148)` 保住；三页无横向溢出。**另补一条此前缺的直接证据**：本机无 Calibre 书库时 `/` 会 500（`calibre_db.session is None`，环境限制不是代码回归），改用 `test_client` 桩掉 `fill_indexpage` 后真渲染首页 → **200 且 HTML 里确实出现 `id="difficulty-entry"`**，证明 R213-A 改版后难度入口仍在书墙上方。共 29 项断言全绿。第二次 merge（R214）后再复跑相关模块 = **98 passed / 0 failed**（我方 3 个测试文件 + 引导/伙伴/成就/阅读设置/i18n/R213 首页与进度 + R214 详情页与 `dc:language` 用例）。清场后临时产物（桩服务、headless profile、脚本）已全部删除，未入库。
- **文档四问**：L1 改 `readme/readme.md`（快速开始加 `/me`、难度入口、引导只弹一次）+ `readme/reading.md`（主题同步）+ `readme/library.md`（首页难度入口）+ `readme/companion.md`（伙伴＝外观）+ `readme/learning.md`（指向引导 L3）；L2 `reading/interface.md` 新增 §4 三条 UI 偏好代理映射与失败口径；L3 新建 `learning/features/onboarding.md`、`reading/features/reader-theme-sync.md`、`companion/features/buddy-ip-risk.md`（companion 首个 `features/`）；LLD 状态行由「开发中」回填「已开发待验收」。
- **与并行会话 R214 的交叠（第二次 merge）**：`cps/web.py`（他们的详情页/阅读入口解禁 vs 我方 `/me` 路由）自动合并通过；`docs/product/readme/library.md` 双方在「能做什么」同一位置各加一条 → 手工两条都留；`plan.md` 他们补 MB-11..15 与我方 MB-15 行合流（复核无重复行）；`response.md` 三处冲突按上条口径解决。合并后重跑无头复验与相关测试（见下条）。注：我方为校验文档链接顺手修出的 `admin/features/oidc-self-registration.md` 与 R213 三份设计文档共 5 条悬空相对路径，与 R214 会话当时正在改的文件有重叠，已随本仓 docs commit 落地。
- **与并行会话 R213 的交叠（按纪律处理）**：merge `origin/develop`（`c9282b4b`）时在 `epub.js`、`index.html`、`read.html`、`web.py`、`reading/interface.md`、`readme/reading.md`、`plan.md`、`requests.md` 与 zh `messages.po/.mo` 相遇。PO 是双方在同一位置各追加一批词条 → 手工保留两段（不用自动合并赌语义），`.mo` 二进制必然冲突，改由 PO 重新编译产出。合并后 R216 的 hooks（`ui-prefs.js` 引用、`__mbReaderTheme` 初值、难度入口 include）逐条复核仍在，相关模块复跑 81 绿。
- **占号与驻留**：R216 占号 commit `9e06cbc2` 已在 `origin/develop`（本轮无需再占号）；跨仓 moon-well 侧原按 R207 开工，**后让号为 R208**（详见「编号」条）。worktree `../magicbook-r216-onboarding-prefs`（分支 `feat/r216-onboarding-prefs`，基线 `57101027` → 三次 merge `origin/develop`：`c9282b4b` R213、`040b627b` R214/R217、`453bb2cd` R215/R218/R219；实现 commit `4dcf82a2`）与 `../moon-well-r208-ui-prefs`（分支 `feat/r208-ui-prefs`，基线 `e9fcc1b`，实现 commit `20a879c`）驻留待验收。`user_ui_settings` 表由 moon-well 上线时 `ddl-auto: update` 建立。
- **发布态闸门（用户令「检查 R218 是否已经好了 好了的话push」后执行）**：R218 的两笔修复（`88ba3626` 详情页 500 = `ub.BookShelf.shelf` 是 id 列却被当对象取 `.name`；`8643f8fe` 详情弹窗 AJAX 失败可见）已确认在 `origin/develop`，连同 R215 阅读器改版、R219 占号一起第三次合进本分支。**每合并一次就在新基线重跑全量**（不在旧基线的绿光上推送）：第三次合并（R215/R218）后 magicbook `pytest tests/` **793 passed / 0 failed**、moon-well `mvn clean test` **Tests run: 1500 / 0 failures / BUILD SUCCESS**；第四次合并（R214 子项 B 的 `book_insight` 与段尾工具回退）后复跑 = magicbook **808 passed / 0 failed**、moon-well **Tests run: 1504 / Failures 0 / Errors 0 + BUILD SUCCESS**（moon-well 侧同样先补 gitignored `.env`，否则 minio 那 30 例是假红）。R215 重写过 `read.html`/`epub.js`，我方主题钩子（head 载 `ui-prefs.js`、5 个按钮传 `true`、epub.js 初值与 `magicbook:reader-theme` 监听）由 `test_reader_theme_sync.py` 在全量里重新锁住。
- **push 已执行（2026-10-23 22:0x，用户令「好了的话push」）**：先 moon-well `feat/r208-ui-prefs` → **develop `e03afbe`**（快进 `13f8f22..e03afbe`），后 magicbook `feat/r216-onboarding-prefs` → **develop `634a24c6`**（快进 `d0856025..634a24c6`）。两仓都从各自 worktree 直推分支 tip，**主检出一笔未推的并行工作都没被带出去**（magicbook 主检出还压着 R217 的 `6dcaced0` 与 staged 的 QA 报告；moon-well 主检出的 R207 两笔在我 claim 之前已自行入远端）。
- **现网探针（无需登录的负向证据）**：`/static/js/ui-prefs.js` **200**、`/static/js/me.js` **200**、`/static/js/onboarding.js` 内含 `accountSeen` **9 处**（新代码已上线，不是只看可达性）；`GET /ajax/ui-settings` → **302** 跳登录（路由在、鉴权门在）、`/ajax/ui-settings/reader-theme` 与 `/me/preferences` → **405**（POST-only 形制保住）、`/me` → **302**。跨仓 moon-well `GET /user/ui-settings` 由推前的 **404** 变推后的 **401**——端点确实起来了且要求 JWT。`https://magicbook.haoshenqi.top` 才是现役域名（旧的 `haoyuhang.top` 301 到它）。**余下唯一未验项＝带鉴权的真人跨设备验收**：探针只能证明「路由存在且不裸奔」，不能证明「A 设备关掉引导后 B 设备真的不再弹」。
- **推送顺序与方式**：moon-well **先**（先 `claim.sh moon-well` 占 R208，再推代码到 develop）、magicbook **后**——反过来的话本仓代理拿 404，引导按 fail closed 从此不自动弹、主题不跨设备同步。两仓都从各自 worktree 直接把分支 tip 推成远端 develop（快进），**不动主检出**：magicbook 主检出还 staged 着并行会话的 QA 报告与未推的 R217 合并 `6dcaced0`，moon-well 主检出 develop 还压着他们未推的 R207 两笔——直接推 ref 才不会替别人发布未验收的工作。
- **余下未验项（如实）**：① **真人跨设备验收**——同一账号两台设备只弹一次、换设备主题跟随、`/me` 纯键盘走完三项保存；现网三条端点已由 401/405 探针证明「起来了且受鉴权」，但**引导是否真的只弹一次、主题是否真的跨设备跟随，仍需带 JWT 的浏览器操作**（本轮无头证据全部来自桩上游）；② 现网旧账号的 `view_settings.onboarding` 回填效果只能等上线后看；③ PingCode MB-15 状态流转与 Ship 关联**未写入**（等用户单独确认）；④ 全量 `pytest tests/` 未跑（发布态动作）。
- **窗口（两次轮转叠加，如实）**：我写本条时分支窗口是 10 节，写入后达 11 → 搬走最旧的 R194 与 R195–R202。随后 merge `origin/develop` 才发现 **R214 会话已把同一节 R194 自己搬过一次**（他们的 `response-R194.md` 与我的同名文件 add/add 冲突）——**采纳 develop 侧副本、弃我的重复件**，只保留我新增的 `response-R195-R202.md`。两边轮转叠加后 merge 完窗口仍为 11（develop 侧原本就带着 11 节），续搬最旧的 **R203** → 现 10 节合规。根因与历次撞号同源：**未推分支上的窗口态互相不可见**，搬移前只对自己的工作区计数必然重复。
- **编号让号（用户拍板「我方让号，改 R208」）**：写 response 时发现并行会话已把 moon-well「207 = 书籍 AI 简介 + `/credit/billing` 费率回传」写进他们**本地 develop 的 `requests.md`（未 push）**，他们的 worktree 就叫 `../moon-well-r207-book-intro`——`origin/develop` 当时仍是 `e9fcc1b`，即「未推分支上的号互相不可见」这个老坑第三次显形（前两次：R206/R208、R209/R210）。我方 UI 偏好从未占号，按「已入台账文本一侧保号」让号：**moon-well 侧全部改 R208**（worktree 目录 `git worktree move`、分支 `-m`、LLD 标题、Java javadoc、本仓 6 处跨仓引用），他们那条 207 一字未动。编号只追加不回改，改动只落在我方未推的分支上。
- **收尾（2026-10-23 22:3x）**：① 用户确认真人跨设备验收通过（同账号两台设备只弹一次、`/me` 键鼠可用且生效、难度入口两步内可达）——AC 三条齐；② PingCode 流转 **PJM MB-15（`X3D_PASH`）→ 已完成**、**Ship MAGICBOOK-223（`juAVbmLF`）→ 已完成**，MB-15 描述尾部追加「交付与验收」段（上线 sha、双闸门数字、现网探针、IP 登记文档路径）；③ 按 worktree 闸门清理 `../magicbook-r216-onboarding-prefs`（分支 `feat/r216-onboarding-prefs`）与跨仓 `../moon-well-r208-ui-prefs`（分支 `feat/r208-ui-prefs`），均 `worktree remove` + `branch -d`（分支内容已是远端 develop 的祖先，`-d` 自然通过）。
- **总结**：requests.md 条目 216 为已占号需求，本条为回应；冲突记录：无撞号；与 R213 / R214 / R215 三轮文件级交叠按 merge 处理并逐条留证；跨仓 moon-well 编号让号（R207 → R208）见「编号」条。

## 2026-10-23（R217：注册后自动回 magicbook——邀请注册接回 OIDC 上下文，enrollment 完成后静默授权回站且已登录）

### R217（用户：「3需要做」——上轮四项遗留中唯一要开发的一项）

- **问题**：R103 起登录页「注册账号 Sign up」按钮直接指向 Authentik 邀请链接且 `target="_blank"`。用户注册完停在 **Authentik 侧**，必须自己切回 magicbook 再点一次「Log in」——**注册与登录是断开的两步**，新窗口更让「注册完该去哪」变成断点。这与 16:00 产品决策（注册必须在 OIDC 上下文中发起，enrollment 完成后 OIDC 继续 → 自动回站且已登录）直接对应。
- **先摸机制再动手**（读源码 + 现网实测，不凭印象）：① Authentik flow 结束时 `next` **硬性要求相对路径**——`authentik/flows/views/executor.py` 的 `_flow_done()` 里 `if next_param and not is_url_absolute(next_param)`，绝对 URL 会被拒为 "Invalid next URL"（`is_url_absolute` = `urlparse(url).netloc` 非空）；② `next` 从 `session[SESSION_KEY_GET]` 取，该值由 `request.GET.get("query")` 解析，前端 `ak-flow-executor` 用 `window.location.search.substring(1)` **整段**透传，故 `next` 能存活到 flow 结束；③ `invitation-enrollment` 末位 stage 是 `UserLoginStage`（`django.contrib.auth.login()`），**flow 结束前已建 Authentik 登录态**；④ OIDC `authorization_endpoint` 与 flow **同域**，故 `next` 可写成相对路径 `/application/o/authorize/?...` —— 正好绕开「必须相对路径」这条硬约束。
- **方案**：`next` 指向**同域 authorize 端点**而非 magicbook callback——由 Authentik 负责「已登录 → 签发 code → 302 回 magicbook」，magicbook 侧 `callback()` **零改动**，建号/绑号/角色判定（R211 已定稿）不分叉。`state`/`nonce`/`code_verifier` 存 magicbook 的 Flask session，复用 authlib 的 `create_authorization_url()` + `save_authorize_data()`，与既有 `/oidc/login` 路径一致。
- **itoken 来源**：**不新增** `AUTHENTIK_ENROLLMENT_INVITE_TOKEN`，改为从既有 `AUTHENTIK_ENROLLMENT_INVITE_URL` 的 query 里解析（兼容 `itoken` 与 `token` 两种 key）——避免「invite URL 与 invite token 两份配置各自漂移」，轮换仍只改一处。解析不出则 flash 错误回登录页，**不静默跳坏链接**。
- **开放重定向防护**：用户可控的只有「注册完回 magicbook 哪个页面」，走 `get_redirect_location(next, "web.index")`（复用 `cps/redirect.py` 的 url_map 白名单校验），只允许站内相对路径。授权 URL 的 path 固定取自 discovery 的 `authorization_endpoint`，**不接受外部输入**。
- **变更点**：`cps/oidc.py` 新增 `GET /oidc/signup`（+ 两个辅助函数 `_invite_token` / `_signup_authorize_target`）；`cps/web.py` 登录页注入 `authentik_signup_url`；`cps/templates/login.html` 按钮改指向 `/oidc/signup` 并**去掉 `target="_blank"`**（同窗口连续体验）；新增 `tests/test_oidc_signup.py` 16 条；`tests/test_login_invite_link.py` 同步更新断言（R103 旧断言「裸邀请链接 + target=_blank」与新行为**有意冲突**，按 R217 行为变更改写）。
- **验证（两轮，都不只看绿灯）**：① 单测——16 条新增 + 相关回归（`test_oidc.py` / `test_login_invite_link.py` / `test_oidc_admin_role.py` / `test_smoke.py` / `test_i18n_seed_contract.py`）**49 passed / 0 failed**；② **反向变异两次实测报红**：next 不剥 scheme+host → 2 条红；next 编码保留 `&` → 3 条红。**第一次变异无效**（把 `quote(target, safe="")` 改成 `safe="/"`——`quote` 默认 `safe="/"` 已编码 `&`，两次变异等价，测试当然不红），改用 `safe="&"` 才是真正改坏语义——**变异必须真的改坏，否则「守卫生效」是假象**。
- **现网端到端实证（不止于单测）**：用与代码同构的 URL 在 `account.haoshenqi.top`（Authentik 2025.10.2）跑完整链路——① executor 入口返回 `ak-flow-redirect`，其 `to` 中 query 完整保留 `next`（双重编码）；② 对照组「不带 next」同样返回 `ak-flow-redirect`，证明这是**正常首阶段跳转而非错误响应**；③ 逐 stage POST 建号后，flow 结束返回 `{"component":"xak-flow-redirect","to":"/application/o/authorize/?client_id=..&state=..&nonce=..&redirect_uri=.."}`——**next 被精确还原为相对路径的 authorize URL**，未触发 "Invalid next URL"，`&` 也未被提前截断；④ 跟随该 redirect → 302 到 `default-provider-authorization-explicit-consent`，consent 阶段的 `pending_user` 正是刚注册的新用户；⑤ 提交 consent → flow 结束返回 `{"to":"https://magicbook.haoshenqi.top/oidc/callback?code=..&state=.."}`——**Authentik 已签发 code 并准备回调 magicbook**，链路终点达成。实测用的测试账号与 consent 记录已清理。
- **踩坑（如实记）**：Authentik executor 的 POST 需 CSRF，header 名是 **`X-authentik-csrf`**（`CSRF_HEADER_NAME = "HTTP_X_AUTHENTIK_CSRF"`）**而非**常见的 `X-CSRFToken`，且必须同时带 `Referer`；取 cookie 值本机 `grep` 不支持 `-P`，改用 `awk '/authentik_csrf/{print $NF}'`。另：本机 `pytest` 并发跑同一 `TMPDIR` 会撞 `EEXIST: mkdir …/pytest-of-root` 报 4 个 ERROR，**与被测代码无关**（tmpdir 竞争），改独立 `TMPDIR` 后 49 条全绿。
- **一处需用户拍板（未擅改）**：magicbook provider 的授权 flow 是 `default-provider-authorization-explicit-consent`，**新用户首次授权会看到一个 consent 确认页**（老用户 30 天内免重复确认）。该环节与「注册→回站」链路本身无关，但要做到**完全无感**需把 provider 授权 flow 改为 `default-provider-authorization-implicit-consent`——属现网配置调整，**不在本条范围，已在 LLD §5 登记待拍板**。
- **文档四问**：能力变了吗 → L3 `docs/product/admin/features/oidc-self-registration.md` 增 § 注册后自动回站；契约变了吗 → 对外**无新接口、无新 env**，登录页注册按钮目标 URL 变化；实现/边界变了吗 → 上述 L3 已含边界条件与实证；本次怎么实现 → LLD `docs/project/iterations/1.0/r217-oidc-signup-return/lld.md`（状态行：已开发，待验收）。另修 KB `docs/kb/instructions/workflows/oidc-login.md`：新增 §1.1 注册链路说明 + §4.5「注册后没回 magicbook」排障 + §4.6 state 失效排障；**并订正一处过时文档**——该文件提到的 `tests/test_user_key.py` **当前仓库不存在**，已加注说明并改指实际文件。
- **窗口**：本条写入使窗口达 11 个 request，按「写入即检查」把最旧的 R195–R202（博客导入链与 TED 导入链盘点修复，19 行）原样搬至 `response-archive/response-R195-R202.md` 并登记索引，窗口回 10；只搬移不改写。
- **驻留与闸门**：worktree `../magicbook-r217-oidc-signup-return`（分支 `feat/r217-oidc-signup-return`，从 `origin/develop` `c9282b4b` 切出）待验收；**push 即触发 fnOS 自动上线**，按用户闸门执行。验收通过后 `worktree remove` + `branch -d`。

## 2026-10-23（R218：R214 子项 A 验收缺陷——在书架里的书详情页 500，读不了书）

### R218（用户：「我为什么没办法读书了」+ 详情弹窗只剩 `...` 的截图 → 定性 → 「可以，按方案修复」）

- **任务定位**：缺陷，挂 R214 子项 A / PJM MB-13 / Ship MAGICBOOK-221。不做无主修复——根因就在 `fdd95225`（子项 A 元数据修正）里。
- **定性证据**（先查 ES 再读码，`app-log-magicbook`）：`Exception on /book/145 [GET]` 栈顶 `web.py:2576 shelf_names=[s.name for s in book_in_shelves]` → `AttributeError: 'int' object has no attribute 'name'`；近 24h `/book/{id}` 9 次、首次 21:07（＝子项 A 部署后）。**影响面按数据切成两半**：`ub.BookShelf.shelf` 是 `Column(Integer, ForeignKey('shelf.id'))`，攒出来的是 id 列表，凡在任意书架里的书必 500；不在书架的书走空列表分支照常打开——所以现象长成「书架里的整架打不开」，极易被误读成个别文件损坏。详情弹窗正文靠 AJAX 填 `/book/<id>`，**「在线阅读」入口就在里面**，500 等于把阅读器入口整个摘掉（`/read/<id>/<fmt>` 路由本身无异常，属可绕过路径）。
- **修复（两 commit）**：① `88ba3626` 名称改由 `_shelf_names_for_book(shelf_ids)` 单查一次（`in_` 一条 SQL，不按书架数 lazy load 出 N+1）；`book_in_shelves` 保持 id 列表不动——`detail.html` 用 `shelf.id in books_shelfs` 判「已加入书架」，形制改了会连带坏掉。② `8643f8fe` 弹窗 AJAX 补 `.fail()`：原先只挂 `.done()`，服务端一报错就停在 `layout.html` 的模板占位符字面量 `...`，把接口故障伪装成「这本书没详情」（ops 准则⑦点名的静默降级形态）；失败分支同时补 `preFilters.remove(useCache)`——原代码只在成功路径摘，一次失败就把 preFilter 永久挂在 jQuery 上污染后续所有 AJAX。文案复用 po 已有 `"Failed to load"`（加载失败），**不新引 msgid、不动 i18n 生成链**（见下「未顺带做的」）。
- **测试**：`tests/test_book_detail_r214.py` 17→**19 条**——真 ORM 造「阶N」书架 + 书-架关联钉住 id→名→解析器整条接线（含空集分支），另加**调用点源码守卫**。Why 要这条：转换器与解析器各自的单测都拦不住「参数形制在调用点错位」，而 §10 计划里那条「集成：真 socket 起 app 打 `/book/337`」子项 A 根本没落地——这正是缺陷漏网的直接原因。反向变异实测三处均报红：调用点换回 `[s.name for s in ...]`、转换器改成 `return list(shelf_ids)`、JS 删掉整个 `.fail` 分支。全量复跑干净 worktree **762 passed / 0 failed**（`layout.html` 是全站布局，不敢只跑改动模块）。
- **同编号互斥的例外（需你知悉）**：R214 的 worktree `../magicbook-r214-book-detail` 已被**子项 B 的 3 个未合并提交**占用（`develop...feat/r214-book-detail` = 3/2），在里面改会把未验收的 B 一起带上线，故另起 `../magicbook-r214-detail-500`（分支 `fix/r214-detail-500`，从 `origin/develop` `040b627b` 切出）。这是对第 9 条「禁止换 slug 绕开」的一次破例，理由不是便利而是**避免把并行在途工作误发布**；子项 B 后续 merge 时会自然拿到本修复（同函数 `show_book` 有冲突面，届时按 B 优先合）。
- **未顺带做的**：跑 `scripts/generate_i18n_seed.py` 会带出不相关的陈旧清单漂移——`cps/static/js/buddy.js`（R206 并行会话合入时漏跑生成器）不在 `tests/i18n_js_files.json` 里、`msgid_count` 299→311。这 12 条词条与本次 hotfix 无关，且把 buddy.js 新纳入契约扫描可能翻出别人的红。已单独记为待办，不在本分支处理。
- **文档四问**：能力变了吗 → L1 无变化（缺陷修复，`readme/library.md` 的「书籍详情」条仍成立）；契约变了吗 → 无对外接口变化；实现/边界 → LLD **§12 新增**（根因/影响面/为何单测没拦住/修法/守卫），§8 降级表补「详情弹窗 AJAX 非 2xx」一行；本次怎么实现 → LLD §12 + 状态行回填缺陷修复。AC 补 **A8**（在书架的书 `/book/<id>` 必须 200）与 **A9**（AJAX 失败可见 + 失败分支摘 preFilter），A1–A7 仍待你真机验收，未代你勾选。
- **驻留与闸门**：worktree `../magicbook-r214-detail-500`（分支 `fix/r214-detail-500`，含 merge `origin/develop` 的 `03a9c991`）原样驻留待验收；验收通过后 `worktree remove` + `branch -d`。**台账占号 R218 已 push**（`4e1aff6f`，纯文档 commit，按「占号即 push」惯例——注意 fnOS 链未加「纯文档跳过」判据，这一推会起一次构建，产物内容与 `040b627b` 等值）。**代码修复本身未 push**，等你的上线指令。
- **窗口**：本条写入后 `## ` 节数达 12，超 10。**本轮不搬移**——`response-R195-R202.md` 的轮转已存在于本地 develop 未 push 的 `6dcaced0` 上（并行会话工作区还 staged 了 `D response-R195-R202.md` / `D response-R203.md`），此处再轮转一次必然与之冲突。登记为待办：待 R217/QA 那批 staged 内容落定后，由一轮统一整理窗口的人按「写入即检查」补齐，不静默滞留。
- **总结**：requests.md 占号 R218（2026-10-23，条目 218，已 push）；本条为回应；冲突记录：与 R214 子项 B 同函数 `show_book` 存在合并冲突面（本分支只动 `shelf_names` 一行 + 新增 helper，B 动 insight 注入，交集小）；与并行会话的 response 归档整理存在窗口轮转撞车风险，已按上条避让。

## 2026-10-23（R212：入口层换皮之品牌资产与字样收敛——一枚圆章两条通道）

- **承接**：用户令「MB-11 authentik 的第 2 项（logo/背景）改成跟 magicbook 统一风格的，看看 magicbook 有没有什么要改的，都使用哈利波特系列风格」。查 MB-11 描述得待办第 1 项即 `branding_logo` / `branding_default_flow_background` 仍是官方默认。
- **先否证「统一风格」的前提**：实测 magicbook **没有任何图形品牌资产**——站内唯一品牌是文字 wordmark（`style.css:223` Grand Hotel 手写体 + 青绿 `#45b29d`），`cps/static/img/` 只有功能图标，`/login` 是裸 Bootstrap `.well`。所以「跟 magicbook 统一」无从取齐，本轮是**新建**图形标识、再让两边共用，不是把 authentik 对齐到某个既有图形。
- **三问三答拍板**：托管＝MinIO `brand/`；标识＝圆章版雪鸮立旧书；范围＝改名 + 挂徽章 + favicon（登录页换皮、整站换色不做）。
- **authentik 侧实测**（决定托管路线）：容器源码 `/authentik/brands/models.py:34` 把 `branding_logo` 等定成 `TextField`，全仓无 `MediaAvatar`、`root/urls.py` 不挂 `/media/`（`/media/`、`/files/` 线上 404）——**没有上传接口，只能填 URL**；登录页 CSP 头实测**不存在**，故跨源图可放行；15 条 flow 的 `background` 列全空 → 改 brand 一处覆盖登录/注册/改密。两条 brand（`authentik-default` / `account.haoshenqi.top`）三个字段现均为内置默认路径。
- **一处主动收紧（对我自己上一轮的方案）**：我先前把「同源一份资产」当成默认前提，实测本仓 CSP 是 `img-src 'self' data:`，且 `tests/test_csp_media.py::test_buddy_image_origin_not_opened_site_wide` 显式断言「其余页面不放行 MinIO」（R181 窄面口径）。为顶栏一枚徽章去放宽全站 img-src 等于推翻一条有意收紧的守卫，不值。故**站内走同源静态文件**（`cps/static/img/brand/`，128px/30KB），认证域走 MinIO，两份产物由 `vibe_images/build_brand_assets.py` 一次生成、不手改。
- **交付项 2 的实测修正**：台账原写「站内 6 处 Calibre-Web」——那是只扫模板。按 `_()`/`N_()` 全量扫，用户可见面 **13 处**（模板 6 + `admin.py` 4 + `helper.py` 5 + `kobo_auth.py` 1 + `search.py` 1，其中 3 处是注册欢迎邮件与测试邮件，站内根本看不见、只有收邮件时看得见）。逐行精确替换，**日志行与文件头许可证署名保留**（前者断了 ES `app-log-magicbook` 文本检索，后者是上游署名）。`stats.html` 的 "powered by Calibre-Web" 亦保留——真实归属，抹掉等于谎报来源。
- **i18n 联动**：改 msgid 必须成对改 `zh_Hans_CN/messages.po` 并重编 `.mo`，否则中文退回英文、看起来像「翻译丢了」。10 条有译文词条成对更新（顺带修上游 `Caliebre` 拼写与 `Catalog`→「路径」两处误译）；3 条无译文的与改前行为一致。
- **顶栏偏移是量出来的**：headless Chrome 实测圆章中线与文字盒中线差 **-0.4px**（35px Grand Hotel 的字形中线低于行框中线），故 `margin: -6px 8px 0 0` 而非直接 `vertical-align: middle`。
- **测试**：新增 `tests/test_brand_consistency.py` 5 例（模板无残留 / 无 `_(...)` 带上游品牌 / 10 词条必须出中文 / 资产存在且被引用且 CSS 有规则 / 配置默认值形态）。**反向变异两处已做**：还原 `http_error.html` + 还原 `.mo` → 2 例即红；复原后 5 passed。开发态合计 **138 passed**（含 `test_csp_media` 8 例，证明没碰坏窄面口径）。全量属发布闸门，留用户指令。
- **不做**：不改 `apple-touch-icon`（140×140 与 64px 素材不匹配，且非本轮范围）；不改 `cli.py --help` 与调试包文件名（运维面）；不给认证页加素材兜底；不放宽 CSP。
- **风险登记**：认证域 logo/背景是**新的对外可见面**，随 `docs/product/companion/features/buddy-ip-risk.md` 同一登记处置（内测可接受、公开注册前换原创）；本轮素材为原创构图，未用电影原图/校徽/闪电字标。
- **上线顺序（不可颠倒）**：moon-well R209 先上线（bucket 策略只在启动时写，不重启 `brand/` 一直 403）→ 传对象并实测 200 → magicbook push → authentik 写三字段 + `restart server worker`（改 brand 有缓存）→ 现网核验。生产 `app.db` 的 `config_calibre_web_title` 现值仍是 `Calibre-Web`（代码默认值改动不影响存量），改它属运维写操作，留用户放行。
- **台账与驻留**：本轮不占新号（属 R212 交付项 2/5 的执行，按「不做无主修复」挂在 MB-11 下）；worktree `../magicbook-r212-brand-assets`（分支 `feat/r212-brand-assets`，基线 `e649a785`）驻留待验收；**push 闸门留用户**。跨仓：moon-well R209（`../moon-well-r209-brand-assets`）。
- **窗口**：本条写入使回应节数达 11，按「写入即检查」把最旧一节 **R205**（单词编故事 Hub 卡）原样搬至 `response-archive/response-R205.md` 并登记索引，窗口回 10。
- **补记（2026-10-24 生产实况）**：authentik 侧**已换皮生效**——两条 brand × 三字段 `UPDATE 2`（改前值备份 `/root/authentik-brands-backup-20261024-r212.json`）+ `restart server worker`（约 10s 回 healthy），headless Chrome 真页面截图确认 `--ak-flow-background` 与 logo/favicon 均指向新对象、圆章实际渲染在卡片正中约 150px（我 mock 里画的左上角小图是错的，素材按 256px 出是对的）。**本仓代码仍未 push**，顶栏徽章/字样收敛只在分支上。另查清一处**非本轮**缺陷：登录按钮仍是英文「Log in」（真人中文浏览器实测，非探针假象），但它不在任何配置面里——2025.10 的 `authentik_flows_flow` 无 `submit_button_text` 列、`flowstagebinding` 无 `label` 列（均实测 schema），R162 中文化覆盖的是 prompt 的 label/placeholder。要改得动上游前端包，另立条目。
- **补记 2（2026-10-24 08:09 已 push 上线）**：用户令「1，2 push，3 改掉吧」→ `8842d1c2..195ab0d7` 快进推 develop（同样从 worktree 直推，主检出有并行会话未提交改动，不碰）。fnOS `build END OK`、基线推进。**线上实测**：`<title>magicbook | Login</title>`、顶栏圆章 + Grand Hotel wordmark 渲染正确（headless Chrome 截图）、`/static/img/brand/{logo,favicon}.png` 双 200。站点标题也按第 3 项改掉：`app.db` → `settings.config_calibre_web_title` = `magicbook`（取拉丁文，Grand Hotel 无中文字形）；该值启动时读入内存，改完当下线上仍吐旧值，由本次部署重启生效——**「改了 DB 就以为好了」是这个坑的标准形态**。
- **合并实况与新基线复跑**：推前 origin 又被并行会话甩开两次（r215 段尾字形、r206 伙伴拖拽）。第一次带来 `messages.mo` **二进制冲突**——正解不是 `--ours/--theirs` 二选一，而是**用合并后的 `.po` 重编**（`.mo` 是产物）；`.po` 侧自动合并后校验「无冲突标记 / 残留 Calibre-Web msgid=0 / 我方 magicbook 词条 11 条」才提交。第二次干净合并。两轮各跑全量：`pytest tests/` = **819 passed / 0 failed**。
- **总结**：requests.md 的 R212 条目追加第二轮拍板与两处实测修正；response.md 增一节、轮转一节。冲突记录：无撞号。

## 2026-10-24（R214 子项 C：整本任务代价面板）

### R214-C（承接「继续」→ 子项 C 开发）

- **任务定位**：R214 收口件，PJM MB-13 / Ship MAGICBOOK-221。三个整本入口（翻译/朗读/详解）
  从「点一下就下单」改成「先看代价再决定」，落 LLD §4.3/§5/§6/§7。
- **后端**：`reading_insight/service.py` 补 `estimate()` + `active_jobs()`；`routes/book_detail.py`
  加 `POST /ajax/whole-book-estimate`（admin + `_llm_task_admin_gate`）；`web.py` 加
  `_credit_billing_rates()`（moon-well `/credit/billing`，5 分钟进程内缓存，取不到回 None）
  与 show_book 的活跃批次快照注入。
- **实现修正（与 LLD 原文不同，已回填 §4.3 表）**：
  ① `units.billable` 新增——翻译/朗读台账的 item 都按 `text_hash` 唯一，拿全书段落数当工作量
  会把重复段算两遍，耗时与积分一起虚高；`paragraphs` 仍保留书目真实段数。
  ② `activeJobs` 新增——§7.5 要的「页面初始进度态」需要服务端承载字段，估算与首屏共用同一个
  `active_jobs()`，两条路径 `total/done` 不会分叉。
  ③ `duration.known` 显式化 + **详解没有常量兜底**（无实测支撑秒/词，样本不足就明说不知道）。
  ④ `credits.rate` 只回传本条链路用到的字段。
  ⑤ 详解覆盖率直接分批调 cached-check，不走 `preview()`（后者会重抽一遍正文；`notWordLike`
  只在预览页有解释位）。
- **前端**：新增 `partials/whole_book_panel.html`（三 tab + 卡片 + 进度条 + 全部文案在 data-*）
  与 `whole-book-panel.js`（切 tab 拉估算并按 kind 缓存、主按钮二次确认带预计时长/积分、
  进度轮询 4s/5s/30s、有活跃批次直接进进度态）；`detail.html` 三个并列按钮合并为单个
  「整本任务」入口并把内联 jQuery 整体迁出；`book-detail.css` 补面板与吸顶进度条样式。
  **详解保持两步式**：面板主按钮只跳 `word_detail_batch_page`，不替管理员下单（R176 边界）。
- **测试**：新增 `tests/test_whole_book_estimate.py` ×10（去重计费单位、朗读不探缓存、
  详解只走 cached-check、lookup 失败不报 0、费率不可得、tts 关闭计费专属原因、历史中位数优先、
  活跃批次透传、非法 kind、空段落）；`test_book_detail_r214.py` 补 5 条（入口 admin 门禁、
  面板三 tab、旧并列按钮不许复活、「不修改原书文件」可见、模板真渲染 + endpoint 存在、
  估算端点只读守卫）。**改了两条既有守卫**：R176 的「三个整本按钮各一处」（形制已合并，
  改判「入口一处 + 面板三 tab」）、R214 自己的 `test_whole_book_buttons_admin_gated`（同因）。
  全量 **804 passed / 0 failed**。
- **未做**：真机验收未跑（面板要真书 + admin 账号）；push 闸门留给你——本节代码在
  `feat/r214-book-detail` 分支上，未合 develop、未 push。
- **窗口**：本条写入后 `## ` 节数再 +1。按上一轮约定（R218 条已说明）轮转待统一整理，
  避免与并行会话的归档改动撞车，本轮不搬移。

## 2026-10-24（R214-C 验收缺陷：入口按钮落进书卡弹层 + 估算 500）

- **现象**：点「整本任务」后页面错乱（整页被套进「书籍详情」弹层）；Console 两条硬事实——
  `/ajax/whole-book-estimate` **500**、`isotope` 报错（后者是弹层里套整页带出来的噪音）。
- **定位一（错乱的真因）**：列表页点书卡是 **XHR 片段**——`show_book` 把 `detail.html`
  渲染成 `fragment.html`，片段没有 `block js`，面板 modal + JS 整块不下发，但按钮在
  `block body` 里照旧渲染。于是 `data-target` 选不到 `#whole-book-panel`，Bootstrap
  data-api 空转并与既有的 `#bookDetailsModal` 抢这次点击 ⇒ 整页被塞进弹层。
  **修**：按钮加 `not is_xhr` 门禁（整本任务只在完整详情页出现）+ 改 JS 显式绑定
  （`preventDefault` / `stopPropagation`），不再依赖 data-api。
- **定位二（500）**：估算链路两处**辅助查询**裸奔——`_history_rate`（台账采样）与
  `active_jobs`（活跃批次）。任一抛错就把整块面板打成 500，而 `.fail` 收到的是 HTML，
  界面只剩「估算失败：500 Internal Server Error」，既不知原因也不知该不该重试。
  **修**：两处各自 try/except 降级（没有样本 / 没有活跃批次 + 落 warning）；路由补兜底
  `except Exception`，落 `traceback.format_exc()` 并把 `类型: 消息` 回给前端——下次再失败，
  面板上会直接写着原因，不用再靠猜。
- **定位三（顺带修的形制级 bug）**：`data-t-start-wordDetail` 属性名带大写，被 HTML
  解析器小写成 `...worddetail`，而 JS 用 `t('start-' + kind)` 取 camelCase ⇒ 详解 tab
  的主按钮文案是空的。模板改全小写、JS 侧 `toLowerCase()`。
- **测试**：新增 5 条（data-api 禁用 / is_xhr 门禁 / 显式绑定 / 键名小写 / 路由兜底源码守卫）
  + 2 条降级行为测试（query 抛错时 `_history_rate` 回 `(None, 0)`、`active_jobs` 回全 None）。
  全量 **853 passed / 0 failed**。
- **待确认**：500 的具体异常类型要等这次上线后看面板上的那行红字（已含异常类型与消息），
  本轮先把「不可读的失败」变成「可读的失败」，再按实际原因收口。

## 2026-10-24（R213-C：首页 `/home` 组装——继续阅读/今日计划/分级推荐/随机发现 + 登录落点开关；A 的侧边栏分组按拍板本迭代不做）

### R213-C（用户令：「A 的侧边栏分组 这个迭代不改，下个迭代再说。直接做C」）

- **范围锁定**：本轮只做 C。R213-A 的「侧边栏四组分组」按用户拍板**本迭代不实施、下个迭代再说**（LLD §5 保留设计与约束，不删不实现），A 以「除分组外已上线」结项。
- **开发第一步先核实 LLD 的两个前置假设**（不猜字段名）：① `writing/history` 是否真带 `createdAt` —— 读 moon-well `WritingVO.HistoryItem` 确认 `createdAt` + `lastDraftNo` 都在，**方案②（moon-well 加 `writingPending`）不启用，跨仓改动为零**；② 待复习词数该取哪个字段 —— `/learning` 页的「到期」用的是 `srs/stats.dueNow`（`learning-hub.js::renderStats`），而 `plan/today` 的 `reviews` 被 `dailyMinutes` 推出的 `reviewCap` **截断**（`LearningPlanService.today()`），拿它会把「到期 40」显示成「到期 20」，直接违反 AC C2。落地取 **`reviewTotal`**——它与 `dueNow` 是同一个 `countDueBetween(MIN, now)` 查询，**数值恒等**，这条同源关系是 C2 的实证依据（不是「大概一致」）。
- **四处对 LLD 原案的修正**（照原文写会错，已回填 LLD §4.3）：见上；另两处是**落点判据抽成 `cps/landing.py::landing_endpoint()` 单点**（四处消费：登录页 `next` 默认值 / 本地登录成功 / OIDC `oidc_next` 默认值 / 已登录再访问登录页；写进 `web.py` 会让 `oidc.py` 只能函数内 import 绕环形依赖）、以及**卡片宏参数化到 7 个参数**（`index.html` 两个循环本来就有差异，不参数化就会在重构中改掉既有观感）。
- **卡片只留一份实现**：新增 `cps/templates/partials/_book_card.html::book_card()`，`index.html`（随机区/列表区）与 `home.html`（继续阅读/分级推荐/随机发现）共用；差异走 `read_flag` / `show_badges` / `card_id` / `modal` / `music_icon` / `series_plain` / `href` + `caller()`（继续阅读用它挂进度条）。**顺带补上 R213-A 的欠账**：格式徽标当初只进了随机区，列表区一直没有——现在两区同源，不会再漂。
- **落点开关带迁移**：`settings.config_home_landing`（Boolean，默认 `True`）。既有库必须靠 `ub.migrate_home_landing_config()` 启动 `ALTER TABLE settings ADD COLUMN ... DEFAULT 1`——缺列不是「回退默认值」而是**任何配置读取都 OperationalError**（整站 500），所以迁移是功能的一部分。管理端「编辑配置」加勾选框（`_config_checkbox`），取消勾选即回退 `/` 发现页，**回退不需要发版**。
- **首页零阻塞**：今日计划完全不走服务端渲染，`home.js` 并行拉两个既有代理端点，单块失败只让该数字显示 `–`，两块都失败才整卡降级为「今日学习页」提示（AC C3）；随机发现沿用 `/` 的 `generate_linked_query + common_filters`，受限书/归档书不会漏出来。文案全部由模板 `_()` 注入 `data-*`，JS 只填数字——**没有第二个取词入口，也就没有「mbT 词条漏进种子」的静默回退面**（`test_home_js_passes_text_through_data_attributes` 钉住）。
- **测试**：新增 `tests/test_home_route.py` 27 例——登录门禁、四块空态不渲染、`阶N` 解析 10 组参数、同阶合并去重、**`阶10` 不排在 `阶2` 前**、已读完不进推荐、书被删跳过、无阶书架进「未分级」尾组、落点开关四种组合、迁移幂等、**真渲染一张卡**（`image.book_cover` / `main_format` 这类过滤器只在渲染时暴露参数不匹配）、**真渲染 index 的一条 entry**（列表区不带格式徽标、带音乐图标）。全量 `pytest tests/` = **873 passed / 0 failed**。
- **两处既有守卫同步更新（有意的结构变更，不是放宽）**：`test_home_nav_shell.py::test_cover_format_badges_present` 与 `test_onboarding_tour.py::test_browse_step_anchors_exist_in_templates` 原来断言 `index.html` 源码里有卡片外层 class / 格式徽标——现在是「index 复用宏」的结构，断言跟着实现移到 `partials/_book_card.html`，并各自加了「index 必须复用宏」这条更强的约束。
- **i18n**：新增 7 条 msgid（Continue Reading / Go to Learning / Recommended by level / Words due for review / Writing tasks to finish / 降级提示 / 配置项标签），`pybabel compile` 重编 `messages.mo`（**msgfmt 报 po 里有三处历史重复词条**：`Save` / `Close` / `Vocabulary` 各定义两次——既有问题，本轮不顺手改，记录备查）。
- **文档四问**：能力变了吗 → L1 `product/readme/library.md` 增「首页（`/home`）」一条；契约变了吗 → **无新对外接口**（`/home` 是页面路由，今日计划复用既有 `/ajax/learning/*` 代理），站点配置新增一项；实现/边界变了吗 → 新建 L3 `product/library/features/home-ia.md`（取数口径、归阶规则、卡片宏、边界与坑）；本次怎么实现 → LLD `project/iterations/1.0/r213-home-ia/lld.md` 补 §4.3 实现修正 + §4.4 验收对应表，状态行改为「A 分组按拍板本迭代不做 / C 已开发待验收」。AC `ac/acceptance.md` C1–C6 逐条勾选并注明判据落点。
- **窗口与合并冲突**：本轮两次触发轮转——① 写入前窗口已 11 节，先把最旧的 **R206 + R207** 原样搬至 `response-archive/response-R206-R207.md`，窗口回 10；② 之后合 `origin/develop`（`d1db8268`，带 R214-C 验收缺陷节）时本文件**必冲突**（双方都往末尾追加），按「两节都保留、按写入时间序 R214-C 在前 / R213-C 在后」解冲突，窗口再达 11，把最旧的 **R208** 搬至 `response-archive/response-R208.md`，窗口回 10。两次均只搬移不改写，索引各登记一行。
- **AC 与台账回填（本轮实际改动的文件，不是只在回应里说）**：`ac/acceptance.md` 状态行改「A 除分组外已上线 / B 已验收 / C 已开发待验收」，C1–C6 逐条勾选并附判据落点 + 测试名，C2/C3 行内标「真机待 G1」；G2/G3 勾选；G1 保留待真机。**A1 明确不勾**并写明「本迭代不实施，不是缺口」；A2–A7/B1–B5 段首注明证据位置但**不代勾**（勾选归 MB-16/MB-17 结项轮次，代勾等于替别人宣布验收结论）。`plan.md` 回填 MB-12（A 除分组外已上线 / B 已验收 / C 已开发待验收）、MB-16（分组按 2026-10-24 拍板本迭代不改，`Shelf.kind` 留待下迭代）、MB-18（已开发待验收 + 落地清单）。
- **顺带发现两处文档欠账（已标注、未擅自修）**：① AC **B6** 写的开关 `reading_progress_enabled` 在仓库里**根本不存在**（`cps/`、`tests/`、`_Settings` 均无命中）——R213-B 从未做过 kill switch，进度上报是常开的。按 MB-17 范围处理，留给下轮确认「补开关」还是「改判据」。② 首版我凭印象写了个 `enable_reading_progress`，随即被自己的核查推翻，已在 AC 里改成「查无此开关」的准确表述——这类名字不能猜。
- **驻留与闸门**：已提交 `f4df325a`，并 merge `origin/develop`（`d1db8268`）拉齐基线，全量重跑后推进 develop 指针（**只推本地 develop，不 push**）。worktree `../magicbook-r213-home-ia`（分支 `feat/r213-home-ia`）保留待真机验收；**push 即触发 fnOS 自动上线，按用户闸门执行**。真机验收重点：G1 两档视口（1440×900 / 390×844）截图比对，以及「今日计划」在 moon-well 正常/不可用两种状态下的表现（C2/C3 的最后一段只能在真机看）。

## 2026-10-24（R221：AI 口语陪练语音优先——教练默认语音条 + 用户录音转写预览）

### R221（用户：修复口语陪练 500；随后「教练默认发语音，类似微信，可以点击语音转文字。同理，我发出去的也是语音，也可以转文字，发送之前先转文字看效果」）

- **编号迁移**：本任务最初误占 **R212**（该号已属品牌资产），已按家族占号流程正式迁移为 **R221**；旧 worktree `../magicbook-r212-speaking-voice` 保留为迁移来源，未删除。R210 口语 403 修复已按用户指令放弃，不推送。
- **教练语音**：开场与每轮回复默认语音条，点击播放、点「转文字」展开原文；自动播放只在开聊/发送的用户手势链中尝试，失败不弹误导框。后端复用阅读 TTS 缓存与计费，前端通过 `/ajax/reading-tts-cached` 不计费回读。
- **用户语音**：录音停止 → ASR 转写 → 可编辑预览 → 点击发送才 multipart 上传并调 LLM；保留「Type instead」。发送失败保留预览与已上传对象名，重试不重复上传。历史会话的用户/教练语音均可回放。
- **修正点**：教练语音合成与回读统一截取 1800 字，避免长回复缓存 miss 后重复扣费；语音按钮文案改为 `Tap to speak`，不暗示按住说话。
- **测试**：JS `node --check` 通过；`tests/test_learning_proxy.py`、`test_learning_pages_static.py`、`test_i18n_seed_contract.py` 回归 **106 passed**。新增「发送失败保留预览」源码守卫。i18n 种子、中文 PO 与 `.mo` 已同步重编。
- **验收缺陷（2026-10-24 续修）**：用户真机验收反馈 `/ajax/reading-tts-cached` 返回正常，但教练与用户语音均无法播放；Chrome 控制台为 `Loading media from 'blob:…' violates ... Content Security Policy`。根因是阅读页已显式放行 `media-src … blob:`，而口语页没有 `media-src`，媒体加载回退到不含 `blob:` 的 `default-src`。修法仅为 `web.learning_speaking_page` 增加 `media-src 'self' blob:`，不改 TTS 接口、不放宽全站 `default-src`，也不向口语页带入阅读页的有道 / MinIO 外源。
- **修复回归**：`tests/test_csp_media.py` 新增「口语 endpoint 只允许 self + blob」与「真实 `/learning/speaking` 路由响应头」两条守卫，并保留无媒体页面不得产生 `media-src` 的反向断言。定向四文件 **116 passed**；JS `node --check` 通过；发布态全量 `pytest tests/` **903 passed / 0 failed**。
- **文档四问**：能力变化 → L1 `docs/product/readme/learning.md`；契约变化 → L2 `docs/product/learning/interface.md`；实现与边界 → L3 `docs/product/learning/features/speaking-voice-first.md`；本次实现 → `docs/project/iterations/1.0/r221-speaking-voice/lld.md`。需求基线已追加 R221，迭代 plan 增 MB-19 工作项。
- **驻留与边界（如实）**：worktree `../magicbook-r221-speaking-voice`，分支 `feat/r221-speaking-voice`；语音优先功能已合入 develop，CSP 验收缺陷修复提交后合并并推送 develop 触发自动上线，worktree 保留待真机验收。尚未完成真人登录态录音、自动播放、历史回放验收。
- **总结**：requests.md 条目 221 为已占号需求；本条为回应。冲突记录：原误占 R212，已迁移 R221；R210 已放弃，不推送。

## 2026-10-24（R222：R214 验收缺陷——生成书籍简介 400，上游 Magpie 403 被误报）

### R222（用户：贴出 `POST https://magicbook.haoshenqi.top/ajax/book-summary 400 (Bad Request)`，「修复这个问题」）

- **任务定位**：缺陷，挂 R214 子项 B / PJM MB-13 / Ship MAGICBOOK-221；不做无主修复。
- **证据链（先查 ES 再读码）**：ES `app-log-moon-well` 在 18:33–18:36 连续记录
  `Magpie call failed: HTTP 403`，同 trace 的 `/book/ai/ability/book-intro` 响应为 500；
  Magpie 容器日志同一时段拒绝 `POST /v1/chat/completions from 172.28.0.1: not on the allow list`。
  moon-well 在 `moon-well_moon-well-net`（172.29.0.2），Magpie 在 `magpie_default`（172.28.0.2），
  跨网段请求到宿主端口时以 bridge 网关 `172.28.0.1` 为源地址，而 Magpie `allowIPs` 只有
  `192.0.0.0/8`。因此 400 是两层误报叠加，不是书籍入参/文件问题。
- **应用修复**：`cps/reading_insight/service.py` 新增 `UpstreamServiceError`（携带上游状态码），
  `_unwrap_result()` 对非 2xx / `success:false` / 不可解析 / 空正文统一抛该异常；
  `/ajax/book-summary` 新增 502 分支并记录上游状态与 message，本地入参/文件错误仍为 400。
  `cps/static/js/book-insight.js` 原本已展示 `data.message`，无需改前端。
- **运行修复**：fnOS `/app/magpie/config/magpie/settings.json` 备份为
  `settings.json.bak-r222-20261024-184438`（600），`allowIPs` 增加 `172.28.0.0/16`；
  `docker compose restart magpie` 后 healthcheck rc=0。未使用 `0.0.0.0/0`，未改端口绑定。
- **验证**：`tests/test_book_detail_r222.py` 四条（上游 500→502 且 message 保留 / 成功仍 200 /
  上游 302 不得当成功 / 非法 book_id 仍 400）+ `test_book_insight.py` +
  `test_book_detail_r214.py`，共 **49 passed**。
  真实链路：从 `moon-well-green` 容器带 gateway key 请求 Magpie `GET /v1/models` → HTTP 200；
  Magpie 重启后无新的 allow-list 拒绝。未伪造生产 AI 简介调用（当前会话无管理员 JWT），
  留给验收时在页面点「生成简介」确认最终 200 与简介落库。
- **文档四问**：能力不变；契约变化 → `/ajax/book-summary` 失败状态从一律 400 改为上游故障 502；
  实现/边界 → LLD §14 + §8；AC B5 改为明确要求 502。L1/L2 无需新增条目（用户操作不变）。
- **窗口**：本条写入后窗口为 11 节，按「写入即检查」把最旧的 **R211** 原样搬至
  `response-archive/response-R211.md` 并登记索引，窗口回 10；只搬移不改写。
- **驻留与闸门**：worktree `../magicbook-r222-book-summary-400`，分支
  `fix/r222-book-summary-400`，基线 `origin/develop` `643eddc8`（含 R222 占号提交），
  实现提交 `b28d9240`，台账回填 `a2056ec5`。用户 2026-10-24 明确指令 push，
  `a2056ec5` 已推送 `origin/develop`；fnOS 链构建/部署成功，运行镜像 label
  `house.build-sha=a2056ec5`，容器 `healthy`。当前 worktree 驻留待真人验收；
  验收通过后 `worktree remove` + `branch -d`。
- **总结**：requests.md 条目 222 为已占号需求；本条为回应。冲突记录：无撞号；已有
  `../magicbook-r214-detail-500` 属 R214 子项 A 的独立 worktree，本任务按新编号 R222 另建，
  未改动既有工作树。

## 2026-10-24（R223：Buddy 悬浮球化——透明头像 + hover 径向快捷气泡，/buddy 可配置）

- **落点**：FAB 结构改 `#ai-companion-fab-wrap`（定位/拖拽/吸附迁 wrap，localStorage 键不变）+
  按钮本体透明头像态（无头像兜底保留蓝底「AI」文字）；删除「AI 伴读」label 与 hover 浮出规则。
  hover/focus 弹出 `.ai-bubble` 径向气泡，弹簧曲线展开；展开方向按 FAB 吸附侧自适应
  （右半屏向左、左半屏向右、贴顶/底时向下/上偏），tooltip 随侧翻边。
- **配置链**：`GET/POST /ajax/buddy/quick-actions`（`cps/routes/buddy.py`），动作全集
  chat/翻译/朗读/书签/学习页/书库/我的，服务端校验 4–5 个且白名单去重；`/buddy` 页 chip 选择器
  （chat 固定不可取消）。存储 `view_settings['buddy']['quickActions']`。label 请求期 gettext
  （导入期冻结只能拿英文 msgid——code review 修正点；另修正 `flask_login`→`cw_login` 导入，
  本仓无 flask_login，函数内 import 在测试环境必炸）。
- **测试**：新增 `test_buddy_page.py` 3 条（GET 全集/默认、POST 持久化、POST 校验不落库）；
  `test_reader_r215_ui.py` 结构断言随 label 删除同步更新；i18n 契约 5 条全绿（zh po/mo 同步重编，
  **只编 zh**——全量 `pybabel compile -f` 会因 it.po 历史 placeholder 错误失败并顺手改写全部 locale，
  已将误编译的其余 locale .mo 恢复）。JS `node --check` 通过。发布态全量 `pytest tests/` =
  **906 passed / 0 failed**。
- **文档四问**：能力 → L1 `product/readme/companion.md` 悬浮球条目；契约 → 站内
  `/ajax/buddy/quick-actions` 新增（记录 LLD）；实现/边界 →
  `iterations/1.0/r223-buddy-fab-bubbles/lld.md`（含触屏无 hover、工具 id 白名单边界）；
  本次实现 → 同 LLD，状态「已开发待验收」。R220 LLD 状态行回填「已上线」。
- **驻留**：worktree `../magicbook-buddy`（分支 `feat/r206-buddy`，与 R220 同分支续作），
  push 后保留待用户验收。
