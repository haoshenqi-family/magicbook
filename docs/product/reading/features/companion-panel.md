# AI 伴读面板布局与状态 · L3 实现说明

> 状态：R215（MB-14）已实现，待验收（2026-10-23）
> 读者：修改阅读器内 AI 面板布局/状态的人。用户可见说明见 [companion.md](../../readme/companion.md)。

## 实现方式

- **布局契约**：`ai_chat.js` 的 `openDrawer/closeDrawer` 维护 `body[data-side-panel="ai"]` 并派发 `reader:panel-open/close`（`detail.kind`）。
  - 桌面：`#ai-companion-drawer` 固定右侧 `50vw`，`#main.reader-main` 缩到剩余宽度；打开/关闭落定后 `dispatchEvent(new Event('resize'))` 让 epub.js 重分页一次。
  - ≤900px：抽屉改为底部 `55vh` sheet（顶部圆角 + 视觉拖拽条），正文不再横向缩宽。
  - 与译文栏互斥：对方打开时只收起自己，不派发 close，避免事件回环。
- **思考中**：`beginThinking()` 在 `sendMessage` 同步路径创建气泡、计时器（每秒刷新 `ai-thinking-elapsed`）与 FAB thinking 动效；页面上下文提取用 `Promise.race` 与 1200ms 超时竞速，超时以空 `pageText` 继续请求；任一 SSE 事件到达 `stopThinking`，`finishMessage` 兜底停表。
- **FAB 语义**：`#ai-companion-fab` 增加品牌色外环与 `#ai-companion-fab-label`（AI 伴读）。移动端首次打开后写 `calibre.ai.fabLabelSeen` 并收起标签，桌面端常显；头像裂图仍回落「AI」文字。
- **placeholder**：模板默认「询问本章内容…」（EPUB）；`ai_page_extract.js` 的 `detectFormat()` 决定 PDF 用「询问当前页…」、TXT 用「询问本文…」。

## 边界条件

- AI 面板的桌面缩宽只对 EPUB 阅读器（`#main.reader-main`）生效；PDF/TXT 仍以 50vw 覆盖，不改它们的布局。
- 顶部 4 个会话操作按钮在桌面显示文字、窄屏只留图标 + `aria-label`/`title`；关闭按钮触达 ≥44px。
- 思考中计时只表示「等待首个事件」的时长，不是模型总耗时；首个 `tool_call`/`delta`/`final`/`error` 任一到达即停表。
