# 积分页分区与明细可读性 · L3

> R245（2026-10-29）建立。相关：L1 [credit.md](../../readme/credit.md)、L2 [credit/interface.md](../interface.md)、
> 本次实现 [LLD](../../../project/iterations/1.0/r245-credit-page-redesign/lld.md)、后端时间兼容 moon-well R229。

## 1. 页面结构

用户积分页 `cps/templates/credits.html` 只组织用户任务；管理员治理独立在
`cps/templates/admin_credits.html` / `/admin/credits`，不再靠同一页的角色显隐承担两类任务：

| 层级 | 页签 | 内容 |
| --- | --- | --- |
| 一级 | 充值 | 余额 Hero 的高频入口与充值档位卡片 |
| 一级 | 积分卡 | 卡密兑换、固定价购卡赠送、已购卡密 |
| 一级 | 明细 | 汇总、筛选和获取/消耗统一流水 |
| 管理 L2 | 积分调整 | 目标用户、金额、原因、到账通知 |
| 管理 L2 | 充值活动 | 起止时间、倍率、发布反馈、活动列表 |
| 管理 L2 | 批量发卡 | 发卡表单、批次列表、批次卡密 |

关键 DOM：

- 用户页签 `#credit-tabs`，面板 `#credit-pane-recharge`、`#credit-pane-cards`、`#credit-pane-details`。
- 用户页根节点 `#credit-page[data-credit-mode="user"]`，不渲染 `#credit-pane-admin`。
- 管理页根节点 `#credit-page[data-credit-mode="admin"]`，页签 `#credit-admin-tabs`，面板
  `#credit-admin-adjust`、`#credit-admin-promotion`、`#credit-admin-cards`。
- 余额快捷按钮使用 `.credit-jump[data-credit-tab]`，只切换已有页签。

## 2. 交互边界

- `showCreditTab(selector)` 先确认目标链接存在，再调用 Bootstrap `tab('show')`；不存在时不抛错。
- 分享卡密写入兑换框后调用 `showCreditTab('#credit-pane-cards')`，确保用户看到的是兑换任务，而不是停留在默认充值页。
- `/credits` 不渲染任何治理表单；`/admin/credits` 先过 `role_admin()`，用户若直接访问得到 403。
- JS 按 `data-credit-mode` 分流：用户页加载余额、档位、卡档位、已购卡与明细；管理页只加载活动、用户候选与发卡批次。
- 两块页面共享代理与样式，但不共享页面 DOM；直接请求管理代理仍由 Flask `role_admin()` 403 与 moon-well 白名单双重拦截。

## 3. 充值活动发布

`promotionWireTime(value)` 只做格式规范化：

```text
2026-10-29T00:00       -> 2026-10-29 00:00:00
2026-10-29T00:00:00    -> 2026-10-29 00:00:00
```

- 不使用 `new Date()`，避免浏览器把无时区的 `datetime-local` 转成 UTC 后再偏 8 小时。
- 不匹配的值原样提交，由服务端返回明确校验错误。
- 发布使用页面共享 `ajax()` 与 `unwrapStrict()`，成功后刷新活动和档位，失败显示 `#credit-promo-feedback`。
- moon-well R229 在 DTO 字段级同时接受 ISO 与空格格式，因此 magicbook 先上线或后上线都不会再次出现 400。

## 4. 明细可读性

`renderConsumeRows()` 不再写内联 `color`，改用语义类：

- 类型徽标：`.credit-type-badge.income` / `.credit-type-badge.consume`。
- 金额：`.credit-amount.income` / `.credit-amount.consume`。

样式要求：

- 获取徽标浅绿底、深绿字和可见边框；金额深绿且加粗。
- 消耗徽标琥珀底、深褐字和深琥珀边框；金额深褐且加粗。
- 任何方向判断都只看 `r.direction === 'INCOME'`，不能按金额正负猜测。
- 颜色只表达方向，不替代文字徽标；色觉差异用户仍可通过「获取/消耗」识别。

## 5. 测试

`tests/test_credit_page_r245.py` 与 `tests/test_account_admin_ia_r251.py` 守卫：

- 用户页只有充值/积分卡/明细三个面板；管理三个面板只出现在 `/admin/credits`。
- `/credits` 与 `/admin/credits` 各自唯一 L2 active，普通用户访问治理页 403。
- 活动提交前调用 `promotionWireTime()`，使用共享 `ajax()`，结果写行内反馈，不使用 `$.ajax()` 或 `window.alert()`。
- 明细使用高对比 CSS 类，JS 不再写内联方向颜色。

关联回归：

```bash
../magicbook/.venv/bin/python -m pytest \
  tests/test_credit_page_r245.py tests/test_credit_card.py \
  tests/test_credit_consume.py tests/test_i18n_seed_contract.py -q
node --check cps/static/js/credits.js
git diff --check
```
