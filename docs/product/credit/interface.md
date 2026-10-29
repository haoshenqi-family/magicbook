# credit · L2 接口说明（magicbook）

> 读者：调用者 / 集成者。本文件只维护 magicbook 积分页对 moon-well credit 域的代理映射与前端消费契约；后端语义权威是 moon-well `docs/product/credit/interface.md`。

## 能力边界

积分页提供余额、充值、积分明细、成就与订阅入口；R242 增加可转赠积分卡的购买、兑换、已购卡密复制/文字分享链接和管理员发卡。magicbook 不保存卡密、不计算价格、不判定卡状态，全部以 moon-well 返回为准。

## 积分卡端点

| magicbook 端点 | moon-well 端点 | 方法 | 超时 | 说明 |
| --- | --- | --- | --- | --- |
| `/ajax/credit/card/packages` | `/credit/card/packages` | GET | 10s | 三档固定价格与面额 |
| `/ajax/credit/card/purchase-order` | `/credit/card/purchase/order` | POST | 10s | 建购卡订单 `{packageId}`，只接受卡档位；随后复用 `/ajax/credit/recharge-pay` 与 `/ajax/credit/recharge-status` |
| `/ajax/credit/card/purchase-list` | `/credit/card/purchase/list` | POST | 10s | 当前用户已购且未作废卡密 |
| `/ajax/credit/card/redeem` | `/credit/card/redeem` | POST | 10s | 兑换 `{key}`；本仓限流 10/min |
| `/ajax/credit/card/admin-issue` | `/credit/card/admin/batches` | POST | 10s | 管理员批量发卡 |
| `/ajax/credit/card/admin-batches` | `/credit/card/admin/batches/list` | POST | 10s | 管理员批次列表 |
| `/ajax/credit/card/admin-cards` | `/credit/card/admin/cards` | POST | 10s | 管理员查看批次卡密 `{batchId}` |
| `/ajax/credit/card/admin-void` | `/credit/card/admin/void` | POST | 10s | 管理员作废未使用卡 `{cardId,reason}` |
| `/ajax/credit/card/admin-export` | `/credit/card/admin/export` | POST | 15s | 管理员导出文本附件 `{batchId}` |

### 鉴权与门禁

- 九条端点全部要求登录；匿名请求按站点规则 302 到登录页。
- 五条管理员端点在代理层先检查 `current_user.role_admin()`，非管理员直接 403，且不得调用上游。
- moon-well 仍按 `credit.admin-user-ids` 白名单二次校验，两层门禁缺一不可。

### 购卡与支付

1. `POST /ajax/credit/card/purchase-order` 只转发 `packageId`，价格与面额由 moon-well 固定档位决定。
2. 返回订单后复用 `POST /ajax/credit/recharge-pay` 获取支付宝二维码，再轮询 `POST /ajax/credit/recharge-status`。
3. 订单 `orderType=CARD` 时支付成功不增加买家积分，只生成一张卡；前端提示「积分卡已生成，请复制卡密」。
4. 前端按本次订单号在 `purchase-list` 中匹配 `purchaseOrderNo` 并高亮新卡。

### 兑换

- 请求：`{"key":"MB-XXXX-XXXX-XXXX-XXXX"}`。
- 成功返回 `credits / balanceAfter / maskedKey`；页面刷新余额、积分明细和已购卡列表。
- 失败统一展示 moon-well `message`（通常为「卡密无效或已兑换」），不区分不存在、过期、作废或已兑换。

### 导出

- `/ajax/credit/card/admin-export` 透传上游 `text/plain` 字节，并返回附件：
  `Content-Disposition: attachment; filename="credit-cards-batch-<batchId>.txt"`。
- 上游非 200 时原样透传错误，不包装成文本成功。

### 分享链接

- 分享页：`GET /credit-card/share`，公开访问，不需要登录。
- 卡密只放在 URL fragment：`/credit-card/share#key=<encodeURIComponent(key)>&credits=<credits>`；fragment 不发送给 Flask、反向代理或访问日志。
- 页面只下发相对路径，前端用 `window.location.origin` 拼绝对链接，避免反向代理协议头不一致时生成 `http://`。
- 分享页不自动兑换，只展示卡密、复制按钮和使用步骤。已登录用户可跳转 `/credits#redeem=<encoded key>`；匿名用户先复制卡密并登录，登录后积分页会从同一标签页的 `sessionStorage` 恢复待兑换卡密。
- 分享页返回 `Cache-Control: no-store`、`Referrer-Policy: no-referrer`、`X-Robots-Tag: noindex, nofollow`。

## 前端消费契约

- `credits.html` 提供兑换区、购卡卡、已购卡密表、管理员发卡区；管理员区只在 `role_admin()` 时渲染。
- `credits.js` 使用统一 `unwrapStrict` 解析 `Result`；导出走独立 blob 路径，不按 JSON 解包。
- 已购/管理员卡密操作分为「复制卡密」和「复制并分享」：前者复制原始卡密，后者复制分享链接。
- 复制优先 `navigator.clipboard.writeText`，失败回退隐藏 textarea + `execCommand('copy')`，两条路径失败都要给用户可见提示。
- 卡密文本使用等宽字体，不渲染二维码或图片。
- `CARD_REDEEM` 在积分明细显示「积分卡兑换」，并计入 INCOME 方向。

## 错误形态

| 场景 | 行为 |
| --- | --- |
| 未登录 | 302 登录页 |
| 非管理员访问管理代理 | 403 `{"success":false,"message":"admin only"}`，不触上游 |
| 空卡密 | 本仓 400，不触上游 |
| 上游业务失败 | 原样透传状态码与 `Result`，页面显示 `message` |
| 复制失败 | 页面提示手动选择卡密复制 |
| 导出失败 | 页面 alert 上游错误，不生成空文件 |

## 相关文档

- 用户手册：[credit](../readme/credit.md)
- 本功能实现：[credit-card](features/credit-card.md)
- 本次迭代：[2026-10-credit-card](../../project/iterations/2026-10-credit-card/credit-card/lld.md)
- 后端契约：moon-well `docs/product/credit/interface.md`
