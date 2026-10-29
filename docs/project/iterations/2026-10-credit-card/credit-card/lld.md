# 积分卡（magicbook R242）· LLD

状态：已上线待验收（2026-10-29，合并提交 `8e0efe95`）
上游：`hld.md`

## 1. 路由

`cps/routes/credit.py` 新增九条薄代理：

| 本仓端点 | moon-well | 方法 | 超时 | 门禁 |
| --- | --- | --- | --- | --- |
| `/ajax/credit/card/packages` | `/credit/card/packages` | GET | 10s | 登录 |
| `/ajax/credit/card/purchase-order` | `/credit/card/purchase/order` | POST | 10s | 登录 + 10/min |
| `/ajax/credit/card/purchase-list` | `/credit/card/purchase/list` | POST | 10s | 登录 |
| `/ajax/credit/card/redeem` | `/credit/card/redeem` | POST | 10s | 登录 + 10/min |
| `/ajax/credit/card/admin-issue` | `/credit/card/admin/batches` | POST | 10s | 登录 + admin |
| `/ajax/credit/card/admin-batches` | `/credit/card/admin/batches/list` | POST | 10s | 登录 + admin |
| `/ajax/credit/card/admin-cards` | `/credit/card/admin/cards` | POST | 10s | 登录 + admin |
| `/ajax/credit/card/admin-void` | `/credit/card/admin/void` | POST | 10s | 登录 + admin |
| `/ajax/credit/card/admin-export` | `/credit/card/admin/export` | POST | 15s | 登录 + admin + binary |

代理只转发白名单字段（不透传请求体多余键）：

- 购卡 `{packageId}`；卡密 `{key}`。
- 管理 `{credits,count,validityDays,longTerm,reason}`、`{batchId}`、`{cardId,reason}`。
- 导出响应重建 `Content-Disposition: attachment; filename="credit-cards-batch-<id>.txt"`。

## 2. 页面

`credits.html` 新增：

- `#credit-card-redeem`：兑换说明、输入框、提交按钮与结果行。
- `#credit-card-packages`：JS 动态渲染三档卡。
- `#credit-card-purchased`：本人卡密表，列为卡密/面额/状态/有效期/操作。
- `#credit-card-admin-panel`：仅在管理员时渲染，包含发卡表单、批次表和卡密明细。

`#credit-page[data-is-admin]` 只用于前端显隐，不承担权限。

## 3. 购卡状态机

```text
click .credit-card-buy-btn
  → buy(packageId, 'CARD', '/ajax/credit/card/purchase-order')
  → createdOrder = unwrap(...)
  → /ajax/credit/recharge-pay
  → currentOrder = {orderNo, packageId, credits, amount, expireTime, kind:'CARD'}
  → QR + countdown + 3s status polling
  → status=1: markPaid()
       → hide checkout
       → 并行刷新余额与已购列表（互不阻塞）
       → loadPurchasedCards(orderNo) 并按 purchaseOrderNo 高亮
       → 按卡密列表是否刷新成功提示复制或“刷新页面后复制”
```

失败处理：

- 建单或预下单失败：`showError`，不覆盖旧 `currentOrder`。
- 余额刷新失败但支付已完成：仍提示卡已生成，并提示刷新页面后复制。
- 状态轮询连续失败 5 次停止，显示错误与「重新下单」。

## 4. 兑换

```text
submit #credit-card-redeem-form
  → 空值：本地提示
  → POST /ajax/credit/card/redeem {key}
  → 成功：清空输入；显示 +credits/余额；刷新余额、明细、已购列表
  → 失败：显示 error.message
  → finally：恢复按钮
```

后端负责规范化大小写、空格和连字符；前端不预处理卡密。

## 5. 管理员

- 发卡：面额固定三档、张数 1–1000、有效期默认 30、长期时清空/禁用天数、原因必填、二次确认。
- 批次：ID/面额/张数/有效期/来源/创建时间，提供查看与导出。
- 卡密：仅 `ACTIVE` 显示作废按钮，作废原因必填。
- 导出：`ajaxBlob` 取二进制，浏览器下载 `.txt`；失败 alert。

## 6. 复制

```text
copyText(text, button)
  ├─ navigator.clipboard.writeText → 成功 done()
  └─ 不可用/拒绝 → textarea + execCommand('copy')
        ├─ 返回 true → done()
        └─ 返回 false 或异常 → showError('复制失败，请手动选择卡密复制。')
```

按钮成功后显示「已复制」1.5 秒，再恢复原文。

## 7. 文案与 i18n

- 模板 `_()` 词条加入种子与中文 PO，只重编译 `zh_Hans_CN/messages.mo`。
- JS 动态文案直写中文，避免账号 locale=en 时回退英文。
- `TYPE_LABELS.CARD_REDEEM = '积分卡兑换'`。

## 8. 测试矩阵

- 匿名用户端点 302。
- 登录普通账号访问五个管理代理 403，且上游调用为零。
- 管理员代理路径与 payload 正确。
- 导出 binary 与附件文件名。
- 页面结构、管理员面板唯一、九条端点、复制 fallback、`CARD_REDEEM`、`purchaseOrderNo`。
- 既有积分消费明细回归。
- `node --check`、i18n 契约、`git diff --check`。

## 9. 边界与部署

- 本仓不持久化卡密，不记录完整卡密日志。
- 已兑换卡仍可在本人已购列表看到状态，但不能再兑换。
- 管理员导出是唯一批量明文出口，必须视为敏感文件。
- 部署顺序：moon-well bootstrap SQL + secret → moon-well → magicbook。
- 本功能无新增 magicbook 数据库迁移。
