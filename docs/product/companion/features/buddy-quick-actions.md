# L3 · 伙伴悬浮球快捷动作（buddy quick actions）实现说明

> 覆盖 R223（悬浮球气泡 + 配置端点）与 R234（AI 对话恒第一位不可删的服务端不变量）。给修改本功能的人读。

## 实现方式

- **端点**：`GET/POST /ajax/buddy/quick-actions`（`cps/routes/buddy.py::buddy_quick_actions`，登录门禁）。GET 返回 `available`（动作全集 + 请求期 `gettext` 翻译 label——依赖请求上下文，勿在模块导入期取词）与 `selected`；POST 覆写选择。存储在 `view_settings['buddy']['quickActions']`（`User.set_view_property`，内部已 commit）。
- **动作全集** `QUICK_ACTION_IDS`：`chat` / `immersive-translate` / `tts-book` / `bookmark`（阅读页，气泡点击转发到顶栏同 id 工具）+ `learning` / `library` / `me`（站点页，气泡点击跳路由）。
- **不变量（R234）**：`_pin_chat_first()` 对写入与读回都做「白名单过滤 + 保序去重 + chat 钉首位」。POST 数量按归一后校验（`QUICK_ACTION_MIN=4`~`QUICK_ACTION_MAX=5`，连 chat 一起算；5 个非 chat＝6 个，400 拒绝不静默截断）；读回对存量旧值同样归一并截上限，归一后不足 4 个或含非法动作回落 `QUICK_ACTION_DEFAULTS`。**改本功能时不得绕过该归一**——「AI 对话恒在第一位且不可删除」是产品铁律（需求基线 §R234）。
- **前端**：气泡渲染 `cps/static/js/ai_chat.js::renderBubbles`（恒 `["chat"].concat(其余)`，与 `initBubbles` 的失败回落默认四项）；配置 UI 在 `/buddy` 页 `cps/static/js/buddy.js::initQuickActions`（chat chip 固定选中、点击无效，最多 5 个、保存校验含 chat ≥4）。

## 边界条件

- 气泡动作「转发 click」依赖阅读页顶栏工具节点（`#immersive-translate` / `#tts-book` / `#tts-book-stop`）存在；改工具 id 时 `dispatchBubbleAction` 白名单需同步。
- 朗读气泡是双态（播放中红底■停止），状态唯一源是顶栏 `#tts-book.active` / `#tts-book-stop`（250ms 巡检），不另建本地状态。
- 直连 API 存的旧值只在读时归一（惰性纠正），库内值在下一次保存前保持原样。
- 展开/tooltip/触屏边界见 R223 LLD `docs/project/iterations/1.0/r223-buddy-fab-bubbles/lld.md`。
