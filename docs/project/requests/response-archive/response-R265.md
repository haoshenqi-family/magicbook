# 回应归档 · R265

## R265 · 站内信新增类型与来源文案（承接 moon-well R235，2026-11-01）

**需求**：moon-well R235 把积分到账从「管理员勾选才发」改成「注册赠送/充值/兑换/购卡全部自动发」，并新增余额不足与归零提醒。本仓是消费侧，必须让这些信在收件箱里能被读懂，而不是掉进 `You have a new notification.` 兜底文案。

**做了什么**

1. `describeMail` 的 `CREDIT_GRANTED` 分支按 `params.source` 分流：新人赠送、充值到账（附订单号）、卡兑换（附卡密掩码）；**没有 source 的历史邮件仍走原通用文案**——线上已经存在 13 封 hedwig/积分信，不能因为新增字段就把老信渲染成空白标题。
2. 三个新分支：`CREDIT_CARD_PURCHASED`（面额 + 掩码 + 有效期，无 `expiresAt` 视为长期有效）、`CREDIT_BALANCE_LOW`、`CREDIT_BALANCE_ZERO`，都跳 `/credits`（白名单已含，无需扩）。
3. 15 条新词条同时落 `i18n_seed.html`、`zh_Hans_CN` PO 并重编译 MO。仓库的 `test_mail_js_translations_are_in_seed_po_and_mo` 会把 mail.js 里每个 `t()` 字面量拿去跟 seed/po/mo 三方比对，漏一处就红——这也是为什么不能只在 JS 里写英文。
4. 新增 Node 守卫 `test_credit_mail_variants_render_by_source_and_type`：直接执行生产 `describeMail`，覆盖 4 种来源 + 3 种新类型 + 历史回退，并断言跳转白名单。

**验证**：`test_mail_ui_r243.py` 25 例、`test_mail_proxy_r243.py`、`test_admin_mail_r250.py` 共 101 例全绿；`test_i18n_seed_contract.py`、积分页/积分卡/明细 34 例全绿。

**未做**：管理员「同时发送到账通知」默认勾选。R243 的守卫用例断言了 `syncAdminNotificationState` 里 `prop('checked', false)`，改默认勾选要连守卫一起改；这是 UX 决策而非缺陷，留给你拍板。

**驻留**：worktree `../magicbook-r265-credit-mail-render`，分支 `feat/r265-credit-mail-render`。
