# HLD — R250 管理员运营站内信后台（magicbook）

> 状态：**开发完成待验收**（2026-10-29）
> 关联：moon-well R230 · 迭代 `1.0` · 需求基线 [`companion requirements`](../../../../product/companion/requirements.md) §3

## 1. 目标

为管理员提供独立运营发信后台，不再把自由正文塞进积分调整表单：

- 选择一人、多人或全体用户；
- 填写标题、500 字纯文本正文与可选站内跳转；
- 预览人数与内容后发送；
- 查看发送历史并整批撤回。

## 2. 页面与权限

- 页面：`GET /admin/mail`，`@admin_required`。
- 入口：`/admin` 管理页新增“运营站内信”按钮；不放入普通用户设置菜单。
- 代理：`/ajax/admin-mail/*`，每个代理先 `current_user.role_admin()`，再转发 moon-well。
- moon-well 侧仍校验 `credit.admin-user-ids`，保持双层门禁。

## 3. 页面结构

1. **发送表单**
   - 范围：指定用户 / 全体用户；
   - 用户搜索与多选，显示 `#id 昵称 (email)`；
   - 标题、正文、跳转路径；
   - 实时字数与预计人数；
   - “预览”与“发送”按钮。
2. **预览区**
   - 使用与 `/mail` 相同的纯文本卡片样式；
   - 明确显示“将发送给 N 人”。
3. **发送历史**
   - 时间、范围、标题、目标/成功人数、操作人、状态；
   - 未撤回批次提供“撤回”按钮；
   - 二次确认说明撤回不可恢复。

## 4. 接口

| magicbook | moon-well |
| --- | --- |
| `GET /ajax/admin-mail/users?keyword=&limit=` | `POST /mail/admin/users` |
| `GET /ajax/admin-mail/audience-count` | `POST /mail/admin/audience/count` |
| `POST /ajax/admin-mail/send` | `POST /mail/admin/send` |
| `GET /ajax/admin-mail/campaigns?pageNo=&pageSize=` | `POST /mail/admin/campaigns/page` |
| `POST /ajax/admin-mail/recall` | `POST /mail/admin/recall` |

代理保持 `_moonwell_proxy` 三元组；本地参数校验是唯一二元组分支。

## 5. 用户侧渲染

`MBMail` 新增 `ADMIN_ANNOUNCEMENT` 分支：

- 标题来自 `mail.title`；
- 正文优先 `customMessage`；
- 跳转按钮继续走白名单；
- 不使用 HTML，不把标题或正文拼进 `innerHTML`。

## 6. 关键不变量

1. 只有管理员看到页面、按钮和代理响应。
2. 5000 人上限在页面与服务端双重校验。
3. 页面预览人数不替代服务端结果；以响应中的 `targetCount/deliveredCount` 为准。
4. 撤回只允许整批，按钮只出现在未撤回批次。
5. 任何失败都必须显示上游 message。
6. 不在 localStorage 缓存正文或用户名单。

## 7. 风险

| 风险 | 缓解 |
| --- | --- |
| 全量用户下拉卡顿 | 默认只给前 100 个匹配项 + 关键词搜索；全体模式不加载名单 |
| 管理员误发全体 | 预览显示人数，发送二次确认，服务端上限兜底 |
| XSS | 标题/正文全部文本节点；跳转白名单 |
| 撤回后前端仍显示 | 撤回成功后重新拉取当前页与未读数 |
| 代理绕过页面门禁 | 五个代理逐个 `role_admin()`，moon-well 再验白名单 |

## 8. 文档四问

- 能力：`readme/companion.md` 与 `readme/mail.md`
- 契约：`companion/interface.md`
- 实现：`companion/features/admin-mail.md`
- 本次：本文件 + [LLD](./lld.md) + [AC](./ac/acceptance.md)
