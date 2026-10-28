# 积分卡（magicbook R242）· HLD

状态：开发完成待验收（2026-10-28）

## 1. 能力边界

- 积分页购买三档固定价格积分卡：1000/¥10、5000/¥50、10000/¥100。
- 支付成功生成一张可转赠文本卡密，买家积分不变。
- 任何已登录用户知道有效卡密即可兑换；卡密不绑定账号。
- 已购卡密可在积分页回看与复制；管理员可批量发卡、查看、作废和文本导出。
- 购卡不参与充值倍率活动；只做文本与复制，不做二维码/图片。

## 2. 非目标

- 不在 magicbook 建卡表、生成卡密或计算价格。
- 不做指定受赠人、转赠记录链、退款、续期、部分兑换。
- 不做卡密二维码、图片、分享海报或邮件。

## 3. 架构

```text
credits.html / credits.js
        │
        ├─ 用户：packages / purchase-order / purchase-list / redeem
        └─ 管理员：issue / batches / cards / void / export
        │
        ▼
cps/routes/credit.py（登录、限流、管理员 403、binary 导出）
        │
        ▼
moon-well /credit/card/*
```

本仓只做代理与前端状态机。卡状态、价格、有效期、兑换原子性与卡密加密均以 moon-well 为准。

## 4. 购买与兑换

- 购卡订单复用普通充值支付与轮询；`orderType=CARD` 由后端决定。
- 支付成功后不显示「积分到账」，显示「积分卡已生成」，并按 `purchaseOrderNo` 高亮新卡。
- 兑换成功后刷新余额、积分明细与已购列表；失败统一显示上游 message。

## 5. 权限与安全

- 九条代理全部要求登录。
- 五个管理员端点在代理层 `role_admin()` 403，moon-well 白名单再校验。
- 兑换与建购卡单限流 10/min。
- 本仓不保存卡密；导出二进制透传，附件名固定。
- 复制优先 Clipboard API，降级 `execCommand('copy')`。

## 6. 影响面

| 区域 | 改动 |
| --- | --- |
| 路由 | `cps/routes/credit.py` 九条代理 |
| 页面 | `cps/templates/credits.html` 兑换/购卡/已购/管理员区 |
| 脚本 | `cps/static/js/credits.js` 购卡状态机、复制、管理员闭环 |
| i18n | 模板词条、中文 PO/MO |
| 测试 | `tests/test_credit_card.py` 与契约/消费回归 |

## 7. 上线顺序与回滚

1. moon-well 先配置 `CREDIT_CARD_SECRET` 并执行 bootstrap SQL。
2. 发布 moon-well，验证发卡、兑换、购卡结算。
3. 发布 magicbook，验证代理、页面与复制。

回滚 magicbook 只关闭入口，不影响已售卡密；moon-well 数据必须保留并继续支持兑换。
