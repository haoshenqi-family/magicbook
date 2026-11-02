# L3 · 管理员积分到账通知实现说明

> 覆盖 R243：管理员正数发放积分时可选发送站内信；减法/扣减不发“到账”通知。

## 表单行为

- `credits.html` 在管理员调整表单中新增 `#credit-admin-notify` 与 `#credit-admin-notification-message`。
- 正文是普通 `textarea`，`maxlength=500`，不使用富文本编辑器。
- 金额为空、0 或负数时：复选框取消并禁用，正文清空并禁用。
- 金额为正数时：复选框恢复可用，但默认不勾选；勾选后正文才可编辑。
- 表单成功后执行原生 reset，并调用 `resetAdminNotification()` 恢复“未勾选 + 正文空 + 按当前空金额禁用”的初始状态。

## 提交

`credits.js` 仍调用既有 `/ajax/credit/admin-adjust` 薄代理：

```json
{
  "userId": 7,
  "amount": 500,
  "reason": "campaign grant",
  "notify": true,
  "notificationMessage": "Thanks for joining."
}
```

- `notify=false` 时不附带 `notificationMessage`。
- 确认框明确显示“并发送到账通知”或“不发送到账通知”。
- 代理不拆 payload；moon-well 负责最终权限、正数限制、500 字限制与邮件落库。
- 失败继续显示上游 message，表单值保留供修正。

## 边界

- 不改管理员调整的审计流水语义。
- 不从 magicbook 直接写邮件事实；成功与否以 moon-well 响应为准。
- 负数金额由前端禁用通知，moon-well 仍做服务端拒绝，形成纵深防御。
