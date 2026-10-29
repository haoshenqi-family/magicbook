# LLD — R250 管理员运营站内信后台（magicbook）

> 状态：**已上线待验收**（2026-10-29）
> 上层设计：[hld.md](./hld.md) · 验收：[ac/acceptance.md](./ac/acceptance.md)

## 1. 代码布局

```text
cps/routes/admin_mail.py
cps/templates/admin_mail.html
cps/static/js/admin_mail.js
cps/static/css/admin_mail.css
tests/test_admin_mail_r250.py
```

接线：

- `cps/routes/__init__.py` 注册 `admin_mail`
- `cps/templates/admin.html` 新增入口按钮
- `cps/static/js/mail.js` 新增 `ADMIN_ANNOUNCEMENT` 渲染
- `cps/templates/i18n_seed.html`、zh PO/MO

## 2. 路由

页面：

```python
@web.route("/admin/mail", methods=["GET"])
@admin_required
def admin_mail_page():
    return render_title_template("admin_mail.html", title=_("Admin Mail"))
```

代理：

```text
GET  /ajax/admin-mail/users
GET  /ajax/admin-mail/audience-count
POST /ajax/admin-mail/send
GET  /ajax/admin-mail/campaigns
POST /ajax/admin-mail/recall
```

每个代理：

1. `current_user.role_admin()` 不满足 → 403；
2. 本地校验/归一；
3. `_moonwell_proxy`；
4. 原样返回三元组。

## 3. 用户选项代理

```text
keyword 可选，最长 80 字；
limit 默认 100，上限 500；
转发 {"keyword": ..., "limit": ...}
```

页面默认不加载全量名单；输入关键词后才请求。全体模式只显示“全体用户”，不预取用户列表。

### 全体人数代理

```text
GET /ajax/admin-mail/audience-count
```

转发空 payload 到 moon-well `POST /mail/admin/audience/count`，返回当前 `app_user` 总数。页面在切换到全体模式与发送成功重置表单后重新获取；请求失败时人数保持未知，预览与发送均被阻止，避免把未知人数当作 0 或沿用旧值。

## 4. 发送代理

请求：

```json
{
  "audienceType": "SELECTED",
  "userIds": [7, 8],
  "title": "内测说明",
  "body": "今晚 22:00 进行维护。",
  "actionPath": "/mail"
}
```

本地校验：

- `audienceType` 只能是 `SELECTED` / `ALL`；
- `SELECTED` 的 `userIds` 必须是正整数数组；去重；
- 页面侧提示 >5000，但代理不替服务端截断；
- 标题/正文非空且长度合规；
- `actionPath` 为空或命中白名单。

代理把原值交给 moon-well，由服务端做最终人数与内容校验；任何失败显示上游 `message`。

## 5. 历史与撤回代理

历史：

```text
GET /ajax/admin-mail/campaigns?pageNo=1&pageSize=20
```

- `pageNo` 默认 1，上限 100000；
- `pageSize` 默认 20，上限 50。

撤回：

```json
{"campaignId": 12}
```

- 必须是正整数；
- 不接收 operator，由 moon-well 登录上下文决定；
- 成功后前端重新加载历史当前页与 `MBMail.refreshUnread()`。

## 6. 页面状态机

```text
compose: editing | previewing | sending
history: loading | ready | error
users: idle | loading | ready | error
```

- 发送按钮在 `sending` 时禁用；
- 预览必须显示标题、正文、按钮文案与目标人数；
- 发送成功后清空表单、显示 campaignId、刷新历史；
- 全体模式编辑标题/正文只使预览失效，不丢弃已取得的精确人数；未知人数或人数 >5000 时不得预览/发送；
- 发送失败保留表单内容，便于修改重试；
- 撤回成功后刷新当前页，不乐观删除行。

## 7. 用户侧 `ADMIN_ANNOUNCEMENT`

`mail.js`：

```text
title = mail.title || t("Announcement")
body = customMessage || t("You have a new announcement.")
```

若 `actionPath` 不在既有白名单，则不生成按钮。标题与正文均用 `textContent`。

## 8. 安全

- 页面与五个代理都要求管理员。
- 所有 POST 带 `X-CSRFToken`。
- 不在 localStorage 存名单或正文。
- 不把上游 title/body 传给 `innerHTML`。
- 用户选项只读 `userId/username/nickname/email`，不展示其他账户字段。

## 9. 测试

### 代理

- 五个代理匿名 302、普通用户 403、管理员可达。
- 三元组透传；本地非法参数 400。
- `send` 只透传白名单字段；`recall` 只透传 campaignId。

### 页面与 JS

- `/admin/mail` 管理员 200、普通用户 403。
- 页面含范围切换、用户搜索、标题/正文/路径、预览、历史、撤回。
- Node 执行纯函数：人数上限、去重、路径白名单、纯文本渲染。
- 全体人数 5000 可预览、5001 被阻止；编辑内容后精确人数不退回 `All users`。
- 发送确认说明可整批撤回，但不声称发送本身不可撤销。
- `mail.js` 支持 `ADMIN_ANNOUNCEMENT` 且不使用 `innerHTML`。

### 回归

- 原 `/mail` 四代理与 `MBMail` 状态不变；新增 `/ajax/admin-mail/*` 五代理。
- 系统事件邮件渲染不变。
- i18n 契约通过。

## 10. 文档回填

- L1 `readme/companion.md`、`readme/mail.md`
- L2 `companion/interface.md`
- L3 `companion/features/admin-mail.md`
