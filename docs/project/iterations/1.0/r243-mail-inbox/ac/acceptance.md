# AC — R243 站内信前端：伙伴信封、抽屉 Mail 与独立收件箱

> 状态：前后端已实现，待用户验收（2026-10-29；合并 R244 `a241f287` 后定向回归 `137 passed`，另 R233 链接/阅读器结构 `19 passed`；未 push、未部署）
> 上层设计：[HLD](../hld.md) · [LLD](../lld.md)

## A. 本轮设计验收

- [x] companion 需求基线记录 R243，并明确产品归 companion、代码使用独立 `mail` 域。
- [x] HLD/LLD/AC 可从迭代目录互相跳转，且引用 moon-well R228 契约。
- [x] 明确伙伴只是邮差，邮件只通知与跳转，不在信内领取。
- [x] 明确未读状态单一来源与三处展示位同步。
- [x] 明确打开 Mail 页签不标已读、展开单封才标已读。
- [x] 明确已解决邮件保留历史但不计未读。
- [x] 明确无后台任务、无 MQ、无 WebSocket、无 localStorage 邮件正文缓存。
- [x] 设计阶段未写实现代码、未建 worktree、未改 L1/L2/L3、未改部署；编码阶段按开发清单执行。
- [x] 用户已于 2026-10-29 确认全部设计口径，可进入 PJM 排期与编码。

## B. 代理与契约

- [ ] `GET /ajax/mail/unread-count` 登录门禁后调用 moon-well `POST /mail/unread-count`，返回三元组。
- [ ] `GET /ajax/mail/page` 将 `pageNo/pageSize` 归一后调用 moon-well `POST /mail/page`，返回三元组。
- [ ] `POST /ajax/mail/read` 校验正整数 `id`，只透传 `id`，返回三元组。
- [ ] `POST /ajax/mail/read-all` 调用 moon-well `POST /mail/read-all`，返回三元组。
- [ ] 所有代理测试桩返回 `(body, status, headers)`；除 `read` 的本地参数校验 400 外，不存在其他二元组返回分支。
- [ ] 匿名访问四个代理不命中 moon-well。
- [ ] 上游业务失败与 503 原样透传，前端能看到 message。
- [ ] `/ajax/credit/admin-adjust` 透传 `notify` 与 `notificationMessage`，既有字段不变。

## C. 伙伴信封与 FAB

- [ ] 有未读且未解决邮件时 FAB 右上出现信封；无未读时隐藏。
- [ ] 信封 `pointer-events:none`，不新增覆盖 FAB 的点击层。
- [ ] 抽屉关闭时，有未读点击 FAB 打开 Mail 页签；无未读打开 Chat。
- [ ] 抽屉已打开时点击 FAB 仍关闭，不重新分流。
- [ ] 未读数请求失败但存在最近一次成功计数时，FAB 仍按旧值分流到 Mail；从未成功时按 0 分流到 Chat。
- [ ] “对话”快捷气泡始终打开 Chat，即使有未读也不进 Mail。
- [ ] FAB 拖拽阈值、吸附、位置记忆、hover 气泡与键盘聚焦无回归。
- [ ] 移动端点击 FAB 仍能进 Mail。
- [ ] 伙伴隐藏后同一未读映射到唤回药丸，可见 FAB 不生成第二个红点；复原后 R243 信封恢复。

## D. 抽屉 Mail

- [ ] AI 抽屉提供 Chat/Mail 双页签，Chat 原会话、输入框、语音与记忆面板无回归。
- [ ] Mail 页签显示最近 5 封、未读数、全部已读与“查看全部”。
- [ ] 打开 Mail 页签本身不调用已读接口；展开单封才调用 `read`。
- [ ] 已读邮件不再显示未读点；已解决邮件保留历史并显示完成状态。
- [ ] 单封已读后未读数减少，FAB、设置菜单、页签 badge 同步。
- [ ] 全部已读后三处角标同步消失。
- [ ] 空态显示“还没有邮件”，错误态显示错误与重试，二者不混用。
- [ ] 未读数接口失败时数字 badge 隐藏并标记不可用，FAB 信封只按最近一次成功计数保留，不伪装成 0。
- [ ] 切回 Chat 再进 Mail 不重复拉取已展开单封正文。

## E. 设置菜单与 `/mail`

- [ ] 设置菜单新增 `top_mail`，仅登录用户可见，带未读数字 badge。
- [ ] 页面 endpoint 为 `web.mail_inbox_page`，分页代理为独立 endpoint；`url_for` 无冲突。
- [ ] `/mail` 仅登录可访问，匿名跳登录。
- [ ] `/mail` 按创建时间倒序分页，默认每页 20，上一页/下一页与页数正确。
- [ ] `/mail` 单封展开、已读、全部已读、空态、加载态、错误态、重试均可用。
- [ ] 已解决邮件在 `/mail` 保留，但不计入未读。
- [ ] `/mail` 的未读数与 FAB、设置菜单、抽屉 badge 一致。
- [ ] 邮件正文按三类模板渲染，参数缺失时显示通用正文而不报错。
- [ ] `customMessage` 覆盖默认正文，HTML/脚本按纯文本显示。
- [ ] 跳转只允许 `/buddy`、`/achievements`、`/credits`；非法路径不生成按钮。

## F. 管理员积分通知

- [ ] 积分表单新增“同时发送到账通知”和可选纯文本正文，最多 500 字。
- [ ] 负数金额时复选框取消、禁用，正文清空并禁用。
- [ ] 正数时通知选项可用但不默认勾选。
- [ ] 勾选后 payload 含 `notify=true`；正文非空时含 `notificationMessage`。
- [ ] 未勾选时不发送通知字段或发送 `notify=false`，不产生邮件。
- [ ] 提交确认框明确提示是否发送通知。
- [ ] 成功/失败沿用现有提示；失败显示上游 message。
- [ ] 表单 reset 后通知控件恢复初始状态。

## G. i18n 与可访问性

- [ ] 所有新增模板文案有 `_()` 与 zh PO/MO 译文。
- [ ] 所有新增 JS `mbT` 字面量进入 `i18n_seed.html` 与生成清单。
- [ ] `tests/test_i18n_seed_contract.py` 全绿。
- [ ] 页签有 `role=tab`、`aria-selected`、`aria-controls`，键盘可切换。
- [ ] 展开卡片是真实 button，带 `aria-expanded`。
- [ ] 信封 `aria-hidden=true`，未读信息由页签与设置 badge 提供。
- [ ] 420px 抽屉与 `/mail` 移动端无横向溢出。

## H. 安全与边界

- [ ] 邮件正文不使用 `innerHTML` 拼接服务端数据。
- [ ] 邮件页与抽屉不把正文写入 localStorage/sessionStorage。
- [ ] 退出登录后不继续显示上一账号邮件。
- [ ] 登录页、注册页、匿名页不显示信封、角标或邮件入口。
- [ ] 无新增 daemon、线程池、定时器、MQ、WebSocket 或持久化任务表。
- [ ] 不改成就即时弹层、伙伴领取/装备、成就领取、积分账户/流水既有语义。
- [ ] `git diff --check` 通过。
