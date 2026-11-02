# R244 · 伙伴动效：隐藏消失动画 + 收信动画（站内信预留钩子）

**状态**：已实现待验收（2026-10-28）

## 1. 需求与拍板

用户：「伙伴增加一个消失的动画和一个收到信件的动画」。三项拍板：
- 消失触发＝**B**：用户点悬浮球上的隐藏 ✕ → 播动画后收起，右缘留唤回小标签（可逆）。
- 收信＝为**后续站内信（R243）**预留：本轮只做展示层 + 可调用钩子，不接数据源。
- 视觉＝**纯 CSS + 一点金光**，不引新素材。

伙伴＝全站 AI 伴读悬浮球（R223 FAB，`#ai-companion-fab`），现状有 idle 呼吸 / thinking 起伏 / sleep 打盹三态。单仓纯前端，moon-well 零改动。

## 2. 改动面

| 文件 | 改动 |
|------|------|
| `cps/templates/ai_chat_panel.html` | fab-wrap 内加 `#ai-companion-hide`（✕）、`#ai-companion-letter`（信封层，含 `.ai-letter-seal`）；wrap 外加 `#ai-companion-restore`（唤回药丸，含 `.ai-restore-spark`/`.ai-restore-label`/`.ai-letter-badge`） |
| `cps/static/css/ai_chat.css` | R244 段：隐藏 ✕（hover/focus-within 显形）；`@keyframes buddy-vanish/buddy-poof/buddy-appear/buddy-letter-fly/buddy-peek`；`.buddy-hidden{display:none}`；唤回药丸样式；信封 + 未读角标（`.buddy-has-letter::before`）；`prefers-reduced-motion` 关全部新动画 |
| `cps/static/js/ai_chat.js` | `hideBuddy/restoreBuddy/initBuddyVisibility/showLetter/clearLetterBadge`；`init()` 挂 `initBuddyVisibility()`、`openDrawer()` 挂 `clearLetterBadge()`；暴露 `window.AICompanion.showLetter` + 监听 `mb:buddy-letter` |
| `tests/test_buddy_animations_r244.py` | 新增 6 条源码守卫 |

## 3. 关键决策与坑

- **为什么同源代理式而非新素材**：与 R206/R223 动效同族，零资产、reduced-motion 可整体降级。
- **信封基础态禁 `visibility:hidden`**：飞入动画只改 `opacity`/`transform`，若 base 写 `visibility:hidden` 而 keyframes 不置 visible，则信封永远不可见（本轮实测踩过，改回靠 `opacity:0` 隐显）。
- **消失/复原双保险**：`animationend` + `BUDDY_ANIM_MS`(700ms) 兜底超时，任一触发即落定；否则 animationend 丢失会让球永久隐藏。
- **收信在隐藏态**：不演飞信，只在唤回药丸打角标——主体动画在隐藏球上无处可演，但信不能丢提示。
- **i18n 零改动**：复用 `_('Close')` / `_('AI Companion')`，图形元素 `aria-hidden`，不新增 msgid，种子/po/mo 与契约测试全不动。
- **未读角标语义**：`showLetter()` 落 `.buddy-has-letter`（球）或药丸角标；`openDrawer()` 清——与「站内信未读」的既有清角标时机一致，R243 可直接沿用。

## 4. 钩子契约（供 R243 站内信对接）

```js
// 有信到达时二选一调用：
window.AICompanion.showLetter();
window.dispatchEvent(new CustomEvent('mb:buddy-letter'));
```
本轮不产生调用方；R243 落地时在「新站内信」事件里调用其一即可，无需改动画层。

## 5. 验证

- 开发态：`test_buddy_animations_r244` 6 条 + buddy 回归（page/no_token/voice/ai_links/i18n_seed/reader_r226）= 48 passed。
- 全量：`pytest tests/` = **1026 passed / 0 failed**。
- 视觉：headless Chrome 载真实 CSS 搭 mock，`--virtual-time-budget` 抓中间帧核对 ✕/金光/信封/唤回药丸+角标（mock 不入仓）。
- 真机验收（待）：悬浮球 hover 出 ✕、点消失→金光消散→右缘药丸、点药丸复原、`showLetter()` 触发飞信+角标、开抽屉清角标、刷新后隐藏态保持、`prefers-reduced-motion` 下无动画但隐藏/唤回/角标仍可用。
