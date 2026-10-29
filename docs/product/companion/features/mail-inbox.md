# L3 · 站内信与伙伴信封实现说明

> 覆盖 R243，R254 起将伙伴邮件从 AI 对话抽屉拆为独立弹层。产品入口归 companion，代码使用独立 mail 域；邮件事实与已读/已解决状态由 moon-well R228 持有。R250 管理员运营发信后台独立见 [admin-mail.md](./admin-mail.md)。

## 实现方式

- **代理**：`cps/routes/mail.py` 注册 `/mail`、`/ajax/mail/unread-count`、`/ajax/mail/page`、`/ajax/mail/read`、`/ajax/mail/read-all`，并在 `cps/routes/__init__.py` 导入注册。四个 JSON 代理只做鉴权、参数归一和转发，成功/失败保持三元组。
- **单一状态层**：`cps/static/js/mail.js` 的 `window.MBMail` 维护 `status / unreadCount / lastKnownUnreadCount / error / lastUpdatedAt`。FAB、设置菜单、独立伙伴邮件弹层和 `/mail` 只订阅这一份状态。
- **载入顺序**：登录态下的 `layout.html`、`read.html`、`readtxt.html`、`readpdf.html` 都在 `ai_chat_panel.html` 前载入 `common/api.js` 与 `mail.js`；匿名阅读不加载 Mail CSS/JS，也不渲染信封、邮件弹层或入口。读取邮件 POST 统一使用 `MBApi.csrfToken()`。
- **伙伴入口**：`ai_chat_panel.html` 在 FAB wrap 内放一个 `aria-hidden` 信封节点，`mail.css` 固定 `pointer-events:none`，不新增覆盖伙伴的点击层。`ai_chat.js` 用纯函数 `chooseFabTarget(panelOpen, unread)` 分流：任一伙伴浮层已开返回关闭，否则有最近成功未读进邮件弹层、无未读进 Chat。
- **快捷气泡**：`dispatchBubbleAction("chat")` 直接 `openDrawer("chat")`，绝不复用 FAB click，避免有未读时“对话”气泡误进邮件。
- **独立弹层**：`#buddy-mail-popover` 是 AI 抽屉外的独立 `role=dialog`，AI 抽屉只保留 `#ai-chat-pane` 与记忆面板。`openBuddyMail()` 先关抽屉，`openDrawer()` 先关邮件弹层，因此两个浮层不会同时出现。
- **邮件预览**：最近 5 封，空态、错误与重试分离；打开弹层只拉列表，不调用已读。单封点击展开后才调用 `MBMail.markRead(id)`；再次打开时保留本页展开状态，已发起的已读不重复。
- **独立页**：`mail.html` 使用 `layout.html` 与同一个 `MBMail`，固定每页 20 封，上一页/下一页、全部已读、空/加载/错误/重试均由状态机渲染。
- **正文**：按 `BUDDY_CLAIMABLE / ACHIEVEMENT_UNLOCKED / CREDIT_GRANTED` 从结构化参数生成 locale 文案；`customMessage` 覆盖默认正文。R250 的 `ADMIN_ANNOUNCEMENT` 读取服务端 `title` 与 `customMessage`，正文缺失时保持空文本，不伪造通用公告。所有动态值都用 `textContent` 或文本节点，模块不使用 `innerHTML`。
- **跳转**：`safeActionPath()` 只放行 `/buddy`、`/achievements`、`/credits`、`/learning`、`/mail`；外链、协议相对地址与危险协议不生成动作按钮。运营邮件无按钮时服务端返回 `actionPath=null`，系统邮件仍按类型派生。
- **刷新**：初始化、`visibilitychange` 可见、`focus`、`pageshow`、打开伙伴邮件弹层时刷新；聚焦请求由 `lastRefreshAt` 做 1 秒去重，不设置 `setInterval`。

## 错误与状态边界

- 未读数失败：`unreadCount=null`，数字角标隐藏，设置入口/邮件弹层进入不可用样式；`lastKnownUnreadCount` 仅供 FAB 信封和 FAB 分流。
- 列表失败：邮件弹层/`/mail` 显示上游 message 与重试，不渲染“没有邮件”。
- 单封已读失败：正文仍可读，卡片内显示错误；下一次重新展开可重试。
- `read` 成功后使用响应 `readAt/unreadCount`；`read-all` 成功后用响应计数更新，并把本次未解决邮件在内存中标记已读。
- `/mail` 页与 FAB 未读状态来自同一 `MBMail`；邮件弹层打开不标已读，展开单封才标已读；退出登录或换页自然销毁内存状态，不使用 localStorage/sessionStorage 缓存邮件。

## 回归边界

- 不改 FAB 的 6px 拖拽阈值、延迟 `setPointerCapture`、吸附/位置记忆、hover 气泡与键盘聚焦。
- 不改原有 Chat 会话、发送、语音与记忆面板逻辑。
- `readcbr.html` 当前没有 Buddy 面板，本轮不扩挂。
- 邮件只通知和跳转，不调用伙伴/成就领取接口，不修改积分账户/流水语义。

## 守卫

- `tests/test_mail_proxy_r243.py`：登录门禁、paging 归一、read 参数、三元组透传、credit 通知字段。
- `tests/test_mail_ui_r243.py`：模板结构、载入顺序、真实 Node 执行 FAB 分流/五路径白名单/纯文本渲染/状态层、i18n。
- `tests/test_common_api_contract.py`：四个挂载 Buddy 的模板 API/Mail/面板顺序。
- `tests/test_i18n_seed_contract.py`：种子、zh PO、编译 MO 一致。
