# LLD — R223 Buddy 悬浮球化（透明头像 + hover 径向快捷气泡）

> 状态：已上线待验收（2026-10-24；真机缺陷修复 `ebf4cec4` 已部署，Chrome 全链路复验通过）

## 1. 需求与范围

用户原话：「把伙伴的AI伴读文字去掉，文字仅悬浮展示即可，蓝边框也去掉」「伙伴的背景也搞成透明的，文字悬浮也去掉，改为悬浮的时候弹出几个（4-5个，在伙伴页面可以设置，默认右上角的 翻译，朗读，书签等功能）功能气泡。类似Iphone 悬浮球。」

- FAB 头像态完全透明：无背景、无边框、无阴影，「AI 伴读」文字标签（常驻与 hover 浮出两版）整体删除。
- 无头像兜底态保留浅蓝底 +「AI」文字（可读性优先，透明只属于头像态）。
- hover / 键盘聚焦 FAB 时弹出径向快捷气泡（类 iPhone AssistiveTouch）：4–5 个动作，在 `/buddy` 页可配置；「对话」气泡固定存在（点击即开 AI 抽屉），阅读页默认 翻译 / 朗读 / 书签 + 对话。
- 不改 AI 抽屉、会话、伙伴头像加载（R206/R220）链路。

## 2. 实现

### 2.1 结构（`ai_chat_panel.html` / `ai_chat.css`）

- 新增 `#ai-companion-fab-wrap` 包裹层：承接原 FAB 的 fixed 定位、拖拽命中区与吸附动画类；`#ai-companion-fab` 退为静态填充（`width/height: 100%`），只负责头像与兜底文字。R223 前拖拽/localStorage 逻辑全在 fab 上，迁移后 `initBuddyFabDrag` 改操作 wrap，其余逻辑（吸附、边缘 gap、位置记忆）不变。
- 新增 `#ai-companion-bubbles` 容器（`pointer-events:none`，展开时子节点恢复）；气泡 `.ai-bubble` 以 CSS 变量 `--bx/--by` 控制径向位移，弹簧曲线 `cubic-bezier(0.34,1.56,0.64,1)` 展开，关闭态加 `visibility` 延迟保证淡出完整。
- 气泡 tooltip 挂 `.ai-bubble-tip`；FAB 吸附到屏幕左半边时 wrap 加 `bubbles-left` 类，tooltip 翻到气泡右侧。

### 2.2 配置接口（`cps/routes/buddy.py`）

- `GET/POST /ajax/buddy/quick-actions`（登录门禁）：GET 返回 `available`（动作全集 + 请求期 gettext 翻译 label）与 `selected`；POST 覆写选择。
- 动作全集 `QUICK_ACTION_IDS`：`chat` / `immersive-translate` / `tts-book` / `bookmark` / `learning` / `library` / `me`；默认 `QUICK_ACTION_DEFAULTS` = chat + 翻译 + 朗读 + 书签（对应用户「默认右上角的翻译、朗读、书签」）。
- 校验：必须 list、去重、全部在白名单内、**长度 4–5**（用户口径 4-5 个）。存储 `view_settings['buddy']['quickActions']`，经 `User.set_view_property`（内部已 commit）。
- label 翻译在请求期执行：`gettext` 依赖请求上下文，模块导入期调用只会缓存英文 msgid（Code Review 实测点）。

### 2.3 前端行为（`ai_chat.js` / `buddy.js`）

- `initBubbles`：GET 配置渲染气泡，失败回落默认四项；`mouseenter`/`focusin` 触发 `openBubbles`，`mouseleave`/`focusout`/外点/开抽屉/拖拽起手均关闭。
- `openBubbles` 展开方向自适应（iPhone 悬浮球同款行为）：按 FAB 吸附位置判定——右半屏向左展开、左半屏向右展开；垂直方向距顶/底不足 94px 时整体向下/向上偏（扇区收窄为 90°），保证气泡永不伸出屏幕。数学换算：屏幕方向向量 `(inward, -vertical)`，气泡位移按 `(cos a, -sin a)` 存储，`a = -atan2(dy, dx)`。
- `dispatchBubbleAction`：`chat` → 触发 FAB click；阅读页动作按同 id 直接 click 顶栏工具（`immersive-translate` / `tts-book` / `bookmark`，复用既有监听与状态机）；站点页动作 `learning` / `library` / `me` → 页面跳转。
- `/buddy` 页新增 chip 选择器（`buddy-qa-*`）：chat 固定选中不可取消，最多 5 个、保存校验 ≥4（含 chat）；文案走 `mbT` + i18n 种子。

## 3. i18n

- 新增 zh 译文 4 条：`Buddy quick actions` / `Pick what pops up around the buddy on hover (4-5). The chat bubble always stays.` / `Pick at least 4 actions` / `Chat`；动作 label（Translation / Read aloud / Bookmark / Daily Learning / Library / Me）复用既有 po 词条。
- JS 侧仅 `buddy.js` 新增 1 条 mbT 字面量，已入 `i18n_seed.html`；`tests/i18n_js_files.json` 清单本就覆盖 `buddy.js`，无需再生。zh `.mo` 只编 zh_Hans_CN（全量 `pybabel compile -f` 会因 it.po 历史 placeholder 错误失败并顺手改写全部 locale，R223 实测踩坑）。

## 4. 测试与守卫

- `tests/test_buddy_page.py` 新增 3 条：GET 全集/默认值/label 非空、POST 持久化并读回、POST 校验（<4 个 / 未知动作 / 重复动作 400 且不落库）。
- `tests/test_reader_r215_ui.py` 结构断言随结构变更更新：label 类必须不存在、wrap 与气泡容器/样式必须存在（有意变更，非放宽）。
- 回归：`test_i18n_seed_contract.py`（种子↔po↔mo 链）、`test_csp_media.py`（CSP 未动）全绿；全量 `pytest tests/` **906 passed / 0 failed**（发布态全量，push 前重跑确认）。

## 5. 边界与已知取舍

### 5.1 真机验收缺陷记录（2026-10-24，已修）

- `pointerdown` 即对 wrap `setPointerCapture` 会把后续 `click` 重定向到 wrap，FAB 开抽屉
  与气泡动作全部失效（拖拽吸附正常，故静态测试不暴露）。修法：捕获延迟到 move 超过
  6px 拖动阈值时设置；`pointermove` 加 `event.buttons & 1` 守卫防悬停误拖。
- hover 悬浮菜单的空隙问题：FAB 与气泡间有约 26px 空隙，`mouseleave` 立即关闭会让
  气泡点不到——350ms 延迟关闭 + 重进取消（悬浮菜单标准做法）。
- 朗读气泡原为单次转发，顶栏播放态是「暂停」而非停止，用户没有可达停止入口。改为双态：
  以 `#tts-book.active` / `#tts-book-stop` 为唯一状态源（250ms 巡检），播放中显示
  红底「■ 停止朗读」并触发 `#tts-book-stop`；空闲恢复「▶ 朗读」。不另建本地状态，
  避免与播放器状态机漂移（起播/暂停/自然播完/手动停止都会同步）。

- 触屏无 hover：移动端 FAB 点击仍开抽屉；气泡在移动端同样渲染但主要服务桌面 hover，后续如需移动端长按展开再迭代。
- 气泡动作「转发 click」依赖顶栏工具节点存在；若未来改工具 id，`dispatchBubbleAction` 的白名单需同步。
- 服务端不强制「chat 必须在 selected 里」：前端渲染恒定注入 chat，POST 即使不含 chat 也不会产生无对话入口的 UI（chat 由 `renderBubbles` 固定插入）。
- 数量口径：用户原话「4-5 个」，服务端按 4–5 校验；2–3 个不落库。
- 展开方向自适应以 FAB 吸附后的几何位置判定（clearRadius 94px），极端小窗口未逐档验证。
