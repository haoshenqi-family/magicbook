## 2026-10-29（R243：站内信前端——伙伴信封、抽屉 Mail、设置入口与独立收件箱）

### R243（用户：「伙伴来接受通知，有通知的时候伙伴头上会出现一个信封，用户点击伙伴可以收信。有个专门的【邮件】（站内信）功能。」）

**对 R243 的回应**：前端已完成并上线，与 moon-well R228 后端组成完整的**伙伴邮差 + 持久站内信**链路；当前处于**已上线待用户真机验收**。

- **代理与契约**：新增 `cps/routes/mail.py` 四条 `/ajax/mail/*` 薄代理，统一登录门禁并保持 `_moonwell_proxy` 三元组；`pageNo/pageSize` 本地归一，`read` 只透传正整数 id，不接收或猜测 `userId`。管理员积分代理透传 `notify` 与 `notificationMessage`，既有字段不变。
- **统一状态层**：`MBMail` 作为 FAB、设置菜单、抽屉页签和 `/mail` 的唯一未读来源，支持初始化、页面可见、窗口聚焦、打开 Mail 页签与 `pageshow` 刷新，不设 `setInterval`。数字 badge 只在成功取得计数时展示；列表加载失败只影响列表局部，保留最近一次成功未读供 FAB 信封判断，不把全局状态误降级为空。
- **伙伴与抽屉**：Buddy FAB 增加 `pointer-events:none` 信封角标，不另盖点击层；抽屉关闭时有未读进 Mail、无未读进 Chat，抽屉已打开仍按原行为关闭；“对话”快捷气泡始终显式进 Chat。AI 抽屉新增 Chat/Mail 双页签，Mail 展示最近 5 封，展开单封才已读，提供全部已读与“查看全部”，打开页签本身不标已读。
- **独立邮件页**：新增登录保护的 `/mail`，倒序分页、单封展开/已读、全部已读、空态、加载态、错误态与重试；正文按结构化参数本地化，服务端字符串只作文本节点，不拼 `innerHTML`；跳转严格限定 `/buddy`、`/achievements`、`/credits`。已解决邮件保留历史但不计未读。
- **设置与管理员**：设置菜单新增 `top_mail` 与未读 badge；积分管理员表单新增“同时发送到账通知”和可选纯文本正文，负数时禁用并清空，成功后与 FAB/设置/抽屉同步计数。`layout`、`read`、`readtxt`、`readpdf` 均已接入；`readcbr` 当前未挂 Buddy 面板，本轮明确不扩展。
- **验证**：合并最新基线后正式发布态全量 **1109 passed / 0 failed / 4 warnings**；合并前邮件/积分/API/i18n/Buddy/阅读器两批定向回归合计 **172 passed / 0 failed**；合并 R244 后重跑 **137 passed / 0 failed**，另 R233 链接/阅读器结构 **19 passed**。`node --check cps/static/js/mail.js`、`ai_chat.js`、`credits.js` 与 `git diff --check` 均通过。moon-well R228 后端全量 **1663 tests** 全绿。
- **文档四问**：能力 → `docs/product/readme/companion.md`；契约 → `docs/product/companion/interface.md`；实现/边界 → `docs/product/companion/features/mail-inbox.md`；本次实现 → `docs/project/iterations/1.0/r243-mail-inbox/`（HLD/LLD/AC 已回填“前后端已实现，待验收”）。
- **R244 语义合并**：再次合并 `origin/develop` 时吸收 R242 收银台和 R244 伙伴隐藏/收信动画。`ai_chat_panel.html` 同时保留 R243 信封/页签与 R244 隐藏、唤回、飞信节点；`ai_chat.js` 的 `openDrawer(tab)` 保留 R243 页签分流并清理 R244 一次性角标；`credits.js` 同时保留 R243 i18n 与 R242 滚动提示。R243/R244 交界采用“同一未读、按可见性映射”：可见 FAB 只显示 R243 信封，伙伴隐藏后显示唤回药丸红点，避免重复提示；信封移到左上避让右上隐藏 ✕。详见 R243 LLD §4.4。
- **发布状态**：merge/push `af9987bb`（`9c6c76dd..af9987bb -> develop`）；fnOS `build END OK`，镜像 `house.code-digest=aafe102a754b1001`，容器 `running/healthy`。生产 `/home` 返回 200；匿名 `/mail` 与 `/ajax/mail/unread-count` 均按预期 302 到登录页。部署时 drift-check 与 webhook 同 sha 双触发，首个 deploy 因容器名竞争失败，构建链自动重试后成功；最终容器 label 与目标 commit 一致。
- **状态与驻留**：worktree `../magicbook-r243-mail-inbox`，分支 `feat/r243-mail-inbox`；实现 `82688cd2`、列表失败隔离修复 `78581165`、前次基线合并 `bf4b6e1a`、R244 合并 `a241f287`、最新基线合并 `79e66e40`、发布提交 `af9987bb`。R243 已上线待用户真机验收；worktree 按验收闸门保留，验收后再清理。
- **窗口与总结**：本条写入时窗口 10 节；合并 R244 后增至 11，按「写入即检查」把最旧 R232 原样搬至 `response-archive/response-R232.md`，窗口恢复 10，并合并 R229/R231 的并行重复索引。requests.md 条目 243 已回填；冲突记录：无撞号，magicbook R228 为另一条既有需求，与本功能无关。

