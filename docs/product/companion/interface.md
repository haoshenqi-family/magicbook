# companion · L2 接口说明

> 读者：调用者 / 集成者。本轮登记 R243 站内信消费侧代理；companion 的 AI 对话、伙伴目录等历史接口仍以文末指针为准。后端邮件事实、幂等、已读/已解决语义唯一权威是 moon-well R228。

## 能力边界

magicbook 只提供登录后的邮件入口、页面、纯文本渲染与薄代理，不创建、不解决、不删除邮件。伙伴、成就和积分邮件只负责通知与跳转，不能从邮件内直接领取。

## 页面

| magicbook 端点 | 方法 | 说明 |
| --- | --- | --- |
| `GET /mail` | 页面 | 登录用户完整收件箱；Flask endpoint 为 `web.mail_inbox_page` |

## JSON 代理

四个代理全部要求 `@user_login_required`。成功与上游失败均原样返回 `_moonwell_proxy` 三元组 `(body, status, headers)`；例外只有 `read` 的本地非法 `id` 校验返回 400。

| magicbook 端点 | moon-well 端点 | 上游方法 | 超时 | 说明 |
| --- | --- | --- | --- | --- |
| `GET /ajax/mail/unread-count` | `POST /mail/unread-count` | POST | 10s | 无 payload |
| `GET /ajax/mail/page?pageNo=1&pageSize=20` | `POST /mail/page` | POST | 10s | `pageNo` 默认 1、上限 100000；`pageSize` 默认 20、上限 50；非法字符串回落默认 |
| `POST /ajax/mail/read` | `POST /mail/read` | POST | 10s | 只接受 JSON 对象中的正整数 `{"id": N}`，不接受 `userId`；非对象、bool/0/字符串/缺失本地 400 |
| `POST /ajax/mail/read-all` | `POST /mail/read-all` | POST | 10s | 空 payload；只影响本人当前未解决未读邮件 |

### 响应形态

- `MailPageVO`：`{records, total, pageNo, pageSize, unreadCount}`。
- `MailUnreadCountVO`：`{count}`。
- `MailReadVO`：`{id, readAt, unreadCount}`。
- `MailReadAllVO`：`{affected, unreadCount}`。
- `MailVO`：`{id, mailType, params, customMessage, actionPath, readAt, resolvedAt, createdAt}`。
- 时间字段均为 epoch milliseconds；`MailPageVO.records` 由服务端按 `createdAt DESC` 返回。

## 前端消费契约

- 未读数、设置菜单角标、FAB 信封与抽屉 Mail 页签只读 `window.MBMail` 的同一状态。
- 页面初始化、重新可见、窗口聚焦、`pageshow`、打开 Mail 页签时刷新；不轮询。
- 未读数请求失败时数字角标隐藏并标记不可用；FAB 只按最近一次成功计数决定是否保留信封。
- `read` / `read-all` 成功后用返回的 `unreadCount` 更新同一状态，不额外请求未读数。
- 邮件正文由前端按当前 locale 渲染结构化参数；`customMessage` 覆盖默认正文，但始终以文本节点显示。
- 跳转只允许 `/buddy`、`/achievements`、`/credits`，其余 `actionPath` 不生成按钮。

## 调用方契约

- 鉴权：当前用户 moon-well JWT 由 magicbook 代理注入，浏览器不接触 token。
- CSRF：浏览器调用本站 POST 代理时必须带 `X-CSRFToken`；`mail.js` 统一从 `MBApi.csrfToken()` 取值。
- 错误：moon-well `Result.message` 必须进入可见错误态，不得把失败渲染为空收件箱。

## 历史接口指针

- AI 对话：[ai-agent 历史设计](../../project/_legacy/feat/ai-agent/design/magicbook-side-design.md)
- 阅读伴读：[ai-reading-companion 历史设计](../../project/_legacy/feat/ai-reading-companion/design/ai-reading-companion-implementation-plan.md)
- 伙伴悬浮球：[buddy quick actions L3](features/buddy-quick-actions.md)
