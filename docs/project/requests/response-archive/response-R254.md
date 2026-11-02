## 2026-10-29（R254：伙伴邮件弹层与 AI 对话抽屉分离）

### R254（用户：「邮件不要出现在AI伴读对话框中。当新邮件到达的时候，点击伙伴弹框显示邮件而不是跟AI伴读公用一个弹框」）

**对 R254 的回应**：已完成并上线。邮件已从 AI 对话抽屉彻底拆为独立伙伴邮件弹层；有未读时点击伙伴进邮件，无未读时进 AI 对话，两个浮层互斥。

- **结构拆分**：`ai_chat_panel.html` 删除 `#ai-companion-tabs`、`#ai-tab-chat`、`#ai-tab-mail`、`#ai-mail-pane` 与抽屉内邮件骨架；AI 抽屉只保留 `#ai-chat-pane`、会话工具与记忆面板。登录态新增独立 `#buddy-mail-popover`（`role=dialog`），含关闭、未读数、全部已读、加载/空/错误/列表与“查看全部”。
- **FAB 路由**：纯函数 `chooseFabTarget(panelOpen, unread)` 保持可执行守卫；无浮层且有未读时 `openBuddyMail()`，无未读时 `openDrawer()`，任一浮层已开时再点 FAB 关闭当前浮层。快捷气泡“对话”仍直接 `openDrawer("chat")`，不复用 FAB 分流。
- **互斥与邮件事务**：`openBuddyMail()` 先关 AI 抽屉，`openDrawer()` 先关邮件弹层；打开弹层只拉最近 5 封，不标已读，展开单封才调用 `MBMail.markRead(id)`；“全部已读”复用 `MBMail.markAllRead()` 并刷新本地预览。设置入口、完整 `/mail`、FAB 信封、伙伴隐藏唤回提示与统一 `MBMail` 未读状态全部保留。
- **视觉与可达性**：桌面为右下独立浮层（宽 `min(420px, calc(100vw - 48px))`，底部给 FAB 留位），移动端 ≤600px 全屏；关闭与全部已读触控目标 ≥44px，列表内部滚动，`[hidden]` 强制隐藏，未新增动画或第二套状态。用真实登录态模板生成本地 Chromium 快照，桌面与移动布局均通过目检。
- **文档四问**：能力 → `docs/product/readme/companion.md`；契约 → `docs/product/companion/interface.md`；实现/边界 → `docs/product/companion/features/mail-inbox.md` 与 `admin-mail.md`；本次实现 → 新建 `docs/project/iterations/1.0/r254-buddy-mail-popover/`（LLD/AC）。需求基线新增 R254，R243 的“双页签抽屉”与 R250 的“抽屉 Mail”历史正文只加被取代/展示注记，不改写原文。
- **验证**：邮件 UI、邮件代理、管理员发信、伙伴动效、i18n、账号 IA、首页壳与 API 契约定向 **138 passed / 0 failed / 2 warnings**；正式发布态全量 **1203 passed / 0 failed / 4 warnings**。`node --check cps/static/js/ai_chat.js`、`mail.js` 与 `git diff --check` 通过；模板/JS 守卫覆盖匿名不渲染、有未读进邮件、无未读进对话、快捷气泡直达 Chat、浮层互斥、打开弹层不标已读、展开单封才已读。
- **上线**：实现提交 `96a756114232d7f1e4e535724549c081cea6a122` 已推送 `origin/develop`（`d7933131..96a75611`）；fnOS `build END OK (96a756114232d7f1e4e535724549c081cea6a122)`，app-manager `deploy SUCCESS`，容器 `running/healthy` 且 `house.build-sha=96a756114232d7f1e4e535724549c081cea6a122`。生产 `/login` 200，匿名 `/buddy` 302 到 `/login?next=%2Fbuddy`。
- **状态与驻留**：**已上线待验收**。worktree `../magicbook-r254-buddy-mail-popover`，分支 `fix/r254-buddy-mail-popover`，实现与部署提交 `96a75611`；按闸门保留待用户验收，验收通过后再清理。
- **窗口与总结**：写入前窗口 10 节，新增后 11；按「写入即检查」把最早 R243 整节原样搬至 `response-archive/response-R243.md` 并在两处归档索引登记，窗口恢复 10。requests.md 条目 254 已从占位回填；冲突记录：无撞号，本轮不改 moon-well 契约。
