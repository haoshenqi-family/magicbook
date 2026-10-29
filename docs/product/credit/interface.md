# credit · L2 接口说明（R243 增量）

> 本文件只登记 R243 为管理员积分调整新增的通知字段。credit 的充值、套餐、流水、活动等其余端点仍以 moon-well 与历史设计为权威，不在本轮伪造完整 L2。

## 管理员积分调整

| magicbook 端点 | moon-well 端点 | 门禁 | 超时 |
| --- | --- | --- | --- |
| `POST /ajax/credit/admin-adjust` | `POST /credit/admin/adjust` | magicbook `role_admin()` + moon-well 白名单二次校验 | 10s |

请求 JSON：

```json
{
  "userId": 7,
  "amount": 500,
  "reason": "campaign grant",
  "notify": true,
  "notificationMessage": "Thanks for joining."
}
```

- `userId`、`amount`、`reason` 是既有字段，语义不变。
- `notify` 可选；缺失按 false，旧请求保持不发送邮件。
- `notificationMessage` 可选、纯文本、最多 500 字；只在 `notify=true` 时透传。
- 只有正数 `amount` 可同时发送到账通知；`notify=true` 且 `amount<=0` 由 moon-well 拒绝。
- 代理不拆 payload，新增字段与既有字段一起原样透传；成功后响应形态保持不变。

## 消费侧契约

- 负数金额时前端取消勾选、清空正文并禁用通知控件。
- 未勾选通知时不发送 `notificationMessage`，避免 UI 与实际上游意图不一致。
- 提交确认框明确显示是否发送到账通知。
- 失败时继续显示 moon-well `Result.message`。
