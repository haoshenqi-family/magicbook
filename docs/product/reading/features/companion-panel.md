# AI 伴读面板布局与状态 · L3 实现说明

> 状态：R215（MB-14）已实现，待验收（2026-10-23）
> 读者：修改阅读器内 AI 面板布局/状态的人。用户可见说明见 [companion.md](../../readme/companion.md)。

## 实现方式

- **布局（2026-10-23 验收回滚）**：`ai_chat.js` 的 `openDrawer/closeDrawer` 只切换 `.open` 类，恢复覆盖式抽屉。
  - 桌面：`#ai-companion-drawer` 右侧 `420px` 固定浮层，覆盖正文；不设置 `body[data-side-panel]`、不缩 `#main`、不触发 epub.js 重分页。
  - ≤600px：`100vw × 100vh` 全屏抽屉（恢复 R215 之前形态），无圆角/拖拽条。
  - 与译文栏不再互斥：AI 浮层直接覆盖右栏，关闭后右栏原样可见。
- **思考中**：`beginThinking()` 在 `sendMessage` 同步路径创建气泡、计时器（每秒刷新 `ai-thinking-elapsed`）与 FAB thinking 动效；页面上下文提取用 `Promise.race` 与 1200ms 超时竞速，超时以空 `pageText` 继续请求；任一 SSE 事件到达 `stopThinking`，`finishMessage` 兜底停表。
- **FAB 语义**：`#ai-companion-fab` 增加品牌色外环与 `#ai-companion-fab-label`（AI 伴读）。移动端首次打开后写 `calibre.ai.fabLabelSeen` 并收起标签，桌面端常显；头像裂图仍回落「AI」文字。
- **placeholder**：模板默认「询问本章内容…」（EPUB）；`ai_page_extract.js` 的 `detectFormat()` 决定 PDF 用「询问当前页…」、TXT 用「询问本文…」。

## 边界条件

- AI 面板对所有阅读器都是覆盖式抽屉（420px / 移动全屏），不改任何阅读器的正文宽度。
- 顶部 4 个会话操作按钮在桌面显示文字、窄屏只留图标 + `aria-label`/`title`；关闭按钮触达 ≥44px。
- 思考中计时只表示「等待首个事件」的时长，不是模型总耗时；首个 `tool_call`/`delta`/`final`/`error` 任一到达即停表。
