# 积分卡（Credit Card）· L3

> R242（2026-10-28）建立。相关：L1 [credit.md](../../readme/credit.md)、L2 [credit/interface.md](../interface.md)、
> 本次实现 [LLD](../../../project/iterations/2026-10-credit-card/credit-card/lld.md)、后端主责 moon-well R227。

## 1. 能力与入口

| 入口 | 位置 | 行为 |
| --- | --- | --- |
| 兑换积分卡 | 积分页「Redeem a Credit Card」 | 输入完整卡密，兑换成功后余额、明细与已购列表刷新 |
| 购买积分卡 | 积分页「Buy a Credit Card to Gift」 | 三档固定价格，购买后走支付宝扫码，支付成功生成一张卡 |
| 已购卡密 | 积分页「My Purchased Card Keys」 | 显示本人购买的卡密、面额、状态、有效期和复制按钮 |
| 管理员发卡 | 积分页管理员面板 | 批量发卡、查看批次、查看卡密、作废、文本导出 |

## 2. 前端实现

**模板** `cps/templates/credits.html`

- 页面根节点 `#credit-page` 通过 `data-is-admin` 暴露当前角色，仅供显隐使用，不替代服务端门禁。
- 兑换表单 `#credit-card-redeem-form`，输入框关闭自动完成与拼写检查。
- 购卡容器 `#credit-card-packages` 由 JS 动态渲染，不在模板硬编码价格。
- 已购表 `#credit-card-purchased-rows` 展示 `key/credits/statusText/expiresAt`。
- 管理员区 `#credit-card-admin-panel` 只在 `current_user.role_admin()` 时输出，且整页只出现一次。

**脚本** `cps/static/js/credits.js`

- `loadCardPackages()`：加载档位，失败在容器内显示错误。
- `buy(packageId, 'CARD', '/ajax/credit/card/purchase-order')`：复用既有支付二维码与轮询状态机。
- `markPaid()`：订单 `kind=CARD` 时不提示充值到账，改为「积分卡已生成」并调用 `loadPurchasedCards(orderNo)`。
- `loadPurchasedCards(highlightOrderNo)`：按 `purchaseOrderNo` 高亮本次新卡。
- `redeemCard()`：提交卡密，成功后刷新余额、明细、已购列表；失败显示上游 message。
- `issueCardBatch()` / `renderAdminBatches()` / `loadAdminCards()` / `voidCard()` / `exportBatch()`：管理员闭环。
- `copyText()`：Clipboard API 优先，失败回退 `execCommand('copy')`；按钮短暂显示「已复制」。

## 3. 状态与交互

### 购卡支付

```text
点击购买
  → POST /ajax/credit/card/purchase-order
  → POST /ajax/credit/recharge-pay（二维码）
  → 每 3 秒轮询 /ajax/credit/recharge-status
  → status=1：隐藏收银台，提示复制卡密，刷新已购列表并高亮本订单
  → status=2：显示过期，可重新建单
```

购买失败不会覆盖旧订单状态；只有预下单成功后才设置 `currentOrder`，避免半初始化收银台。

### 兑换

- 空输入在浏览器端直接提示，不发请求。
- 提交期间禁用按钮，完成后恢复。
- 成功后清空输入框并显示新增积分与当前余额。
- 上游业务失败原样显示，避免把「已兑换」误报为网络错误。

### 管理员发卡

- 面额下拉固定 1000 / 5000 / 10000；张数 1–1000。
- 有效期默认 30 天；勾选长期后禁用并清空天数输入。
- 原因必填；提交前二次确认张数与面额。
- 发卡成功后刷新批次并自动展示新批次卡密。
- 作废需要填写原因，仅 `ACTIVE` 卡显示作废按钮。

## 4. 代理与安全边界

`cps/routes/credit.py` 新增九条薄代理，全部 `@user_login_required`：

- 用户端点：packages、redeem、purchase-order、purchase-list。
- 管理端点：admin-issue、admin-batches、admin-cards、admin-void、admin-export。
- `redeem` 与 `purchase-order` 加 10 次/分钟限流；管理员端点在代理层先 `role_admin()` 403，再交给 moon-well 白名单复核。
- 本仓不保存卡密、不生成卡密、不计算面额/价格，也不把卡密写入日志。
- 导出使用 binary 透传并重建附件文件名；非 200 不伪装成成功文本。

## 5. 文案与 i18n

- 模板新增 `_()` 词条已加入 `i18n_seed.html` 与 `zh_Hans_CN/messages.po`，并只重编译中文 `messages.mo`。
- JS 动态状态文案（如「购买并赠送」「积分卡已生成」「卡密列表加载失败」）直接写中文；不依赖模板翻译链。
- `TYPE_LABELS` 新增 `CARD_REDEEM: '积分卡兑换'`。

## 6. 测试

`tests/test_credit_card.py` 覆盖：

- 匿名访问用户端点 302；登录普通账号访问五个管理端点 403 且上游零调用。
- 卡密、购卡订单、已购列表、管理员发卡/批次/卡密/作废的上游路径与 payload。
- 导出 binary 与附件文件名。
- 页面结构、管理员面板唯一性、九条 JS 端点、复制 fallback、`CARD_REDEEM` 与 `purchaseOrderNo`。

关联回归：

```bash
../magicbook/.venv/bin/python -m pytest tests/test_credit_card.py tests/test_credit_consume.py -q
../magicbook/.venv/bin/python -m pytest tests/test_common_api_contract.py tests/test_i18n_seed_contract.py -q
node --check cps/static/js/credits.js
git diff --check
```

## 7. 已知不做

- 不做二维码、图片卡、分享海报、邮件发送。
- 不绑定受赠人、不做转赠记录链、不做部分兑换、退款或续期。
- 不在 magicbook 侧保存或校验卡密哈希；兑换权威只在 moon-well。
- 不改普通充值档位、倍率活动与支付回调链。
