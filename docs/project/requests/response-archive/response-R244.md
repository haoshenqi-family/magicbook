# 回应归档 · R244

> 2026-10-29 R250 / R252 合并后窗口达 11 节，原样搬移不改写。

## 2026-10-28（R244：伙伴动效——隐藏消失动画（金光消散）+ 收信动画（站内信预留钩子，纯 CSS））

### R244（用户：「伙伴增加一个消失的动画和一个收到信件的动画」；三项拍板 1B / 2 后续站内信 / 3 金光·纯 CSS）

- **任务定位**：需求（展示层动效），单仓纯前端（`ai_chat.css` + `ai_chat.js` + `ai_chat_panel.html`），moon-well 零改动。伙伴＝全站悬浮球（R223 FAB），现状已有 idle 呼吸 / thinking 起伏 / sleep 打盹三态，但无「消失」与「收信」。
- **三问三答**：① 消失触发＝**B**（用户点悬浮球上的隐藏 ✕，播动画后收起，右缘留唤回小标签，可逆）；② 收信＝**为后续站内信（R243）预留**，本轮只做展示层 + 可调用钩子，不接数据源；③ 视觉＝**纯 CSS + 一点金光**，不引新素材。
- **消失**：悬浮球右上角小 ✕（hover/focus 才显形，平时不抢视线）→ `buddy-vanish`（缩小旋转淡出）+ `buddy-poof`（一圈金色光晕向外扩散消散）→ 收起、右缘 `#ai-companion-restore` 小药丸（✦ + hover 展开「AI Companion」）。隐藏态记 `localStorage calibre.ai.buddy.hidden`，跨页保持；点药丸 `buddy-appear` 反向 materialize 复原。
- **收信**：`#ai-companion-letter` 金边纸 + 火漆印从右上屏外飞入球心（`buddy-letter-fly`），落定后球轻 `buddy-peek` 一下，并落一个红色未读角标（`buddy-has-letter::before`），开抽屉即清。钩子＝`window.AICompanion.showLetter()` + 自定义事件 `mb:buddy-letter`，未来站内信有信时调用即可；伙伴已隐藏时不演飞信，只在唤回药丸上打角标（避免主体动画看不见却让用户以为没到信）。
- **复用仓内范式**：动效族沿用 R206 头像 keyframes / R223 气泡的 transform 分层（外圈 hover 缩放走 button、内圈动效走 img/子元素，互不打架）；未读角标是 R223 气泡 `is-playing` 同类的状态类。
- **i18n 零改动**：隐藏 ✕ 复用 `_('Close')`、唤回标签复用 `_('AI Companion')`，信封/角标纯图形 `aria-hidden`——不新增 msgid，故 i18n 种子/po/mo 与 `test_i18n_seed_contract` 全不动。
- **可访问性/降级**：`prefers-reduced-motion: reduce` 下五个新动画全关、信封 `display:none`；消失/复原除 `animationend` 外都挂 `BUDDY_ANIM_MS` 兜底超时，防 animationend 丢失导致球永久隐藏（fail-safe）。
- **测试**：新增 `tests/test_buddy_animations_r244.py` 6 条源码守卫（keyframes 齐 / reduced-motion 覆盖三个新状态类 / 信封基础态禁 `visibility:hidden`——实测踩过该坑 / 面板三元素齐 / JS 暴露 showLetter+事件+localStorage+兜底 / 不引入新 JS 词条）。开发态回归 `test_buddy_page`+`no_token`+`voice`+`ai_links`+`i18n_seed`+`reader_r226`+本套 = **48 passed**；全量 **1026 passed / 0 failed**。
- **视觉自检**：本机 headless Chrome 载真实 `ai_chat.css` 搭 mock，`--virtual-time-budget` 抓中间帧——✕ 显形、金光消散、金信封（静态帧确认本体样式）、唤回药丸+红角标均正确；mock 仅用于人眼核对，不入仓。
- **交付四问**：能力→用户可见（隐藏/唤回/收信提示），L1 `readme/companion.md` 待补一句；契约→无接口变化（未新增路由/端点）；实现/边界→本 LLD + 守卫注释；本次实现→`iterations/1.0/r244-buddy-animations/lld.md`。
- **台账与驻留**：`claim.sh magicbook` 占号 **R244**（`6462ab70`，纯台账）；worktree `../magicbook-r244-buddy-animations`（分支 `feat/r244-buddy-animations`）驻留待验收；**push 闸门留用户**。窗口：写入前 10 节，按「写入即检查」把最旧 R229 整节原样搬至 `response-archive/response-R229.md` 并登记索引，窗口回 10。冲突记录：无撞号；与 R243（站内信，仅占号未实现）是「动画层 vs 数据层」的分工，本轮只交动画钩子。

