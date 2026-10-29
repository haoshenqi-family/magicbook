# companion / admin-mail · 实现说明

> 状态：magicbook 后台已实现（R250，2026-10-29），moon-well R230 提供运营发信事实与批次审计；整体待验收。

## 代码落位

```text
cps/routes/admin_mail.py
cps/templates/admin_mail.html
cps/static/js/admin_mail.js
cps/static/css/admin_mail.css
tests/test_admin_mail_r250.py
```

接线：

- `cps/routes/__init__.py` 注册 `admin_mail`；
- `cps/templates/admin.html` 增加管理员入口；
- `cps/static/js/mail.js` 支持 `ADMIN_ANNOUNCEMENT` 渲染与五个白名单路径；
- `cps/templates/i18n_seed.html`、zh PO/MO 同步文案。

## 页面与代理

- `GET /admin/mail`：管理员页面，`@admin_required`；页面含范围切换、用户搜索与多选、标题/正文、可选跳转、预览、发送、历史与撤回。
- 五个 `/ajax/admin-mail/*` 代理：`users`、`audience-count`、`send`、`campaigns`、`recall`。每个代理先校验 `current_user.role_admin()`，再调用 `_moonwell_proxy`。
- `users` 只透传 `keyword/limit`；`send` 只透传五个白名单字段，`ALL` 不携带客户端 userIds；`recall` 只透传正整数 `campaignId`。上游 `Result.message` 原样进入页面错误态。

## 人数与发送状态

- 全体人数来自独立代理 `/ajax/admin-mail/audience-count`，不靠加载全量用户列表估算。
- 切换到全体模式、发送成功重置表单后重新获取人数；编辑标题或正文只使预览失效，不丢弃已取得的精确人数。
- 人数未知时禁止预览/发送；人数 >5000 时前端阻止，服务端再次拒绝。
- 发送确认显示精确人数，并说明可整批撤回、但收件人可能已经看到；不误称发送本身不可撤销。
- 发送失败保留表单内容；发送中禁用按钮；成功后刷新历史第一页。

## 历史与撤回

- 历史按发送时间倒序分页，显示时间、范围、标题、目标/成功人数、操作人、正文与撤回状态。
- 未撤回批次显示撤回按钮；二次确认明确「整批消失且不可恢复」。
- 撤回成功后刷新当前历史页与 `MBMail` 未读数；失败显示上游 message，不乐观删除行。
- 已撤回批次不显示按钮；审计记录由 moon-well 永久保留。

## 用户侧渲染

- `mail.js` 对 `ADMIN_ANNOUNCEMENT` 读取 `mail.title` 与 `customMessage`，标题和正文都通过文本节点渲染。
- `safeActionPath()` 只放行 `/credits`、`/buddy`、`/achievements`、`/learning`、`/mail`；服务端读取时也会把非法运营路径归一为 `null`。
- 原 `BUDDY_CLAIMABLE / ACHIEVEMENT_UNLOCKED / CREDIT_GRANTED` 三类系统邮件渲染、未读、已读与已解决语义不变。

## 安全与边界

- 页面与五个代理双层门禁：magicbook `role_admin()`，moon-well `credit.admin-user-ids`。
- 不在 localStorage/sessionStorage 保存正文或收件人名单；不使用 `innerHTML` 拼服务端数据。
- 不做富文本、附件、定时发送、草稿、模板编辑器、回信、打开率/点击率统计、单封撤回或站外邮件。
- 不新增用户侧邮件页面或第二套未读状态；运营邮件仍进入现有 `/mail`、抽屉 Mail、设置入口与伙伴信封。

## 测试锚点

- `tests/test_admin_mail_r250.py`：页面与五代理权限、参数归一、三元组透传、5000/5001、全体人数精确保持、发送确认文案、纯文本渲染、i18n 与 Node 语法。
- `tests/test_mail_proxy_r243.py` / `tests/test_mail_ui_r243.py`：原 `/mail` 代理、FAB 信封、抽屉页签、设置入口与三类系统邮件回归。
- `tests/test_i18n_seed_contract.py`：种子、zh PO、编译 MO 一致。
