# LLD — R255 [缺陷] 注销后 remember_token 未清除，下一次请求自动把用户登回来

> 状态：已上线（2026-10-29 merge/push `81356579`；fnOS 构建部署完成，容器 healthy；待用户验收）
> 迭代：1.0 · 来源：用户 sunny 反馈「接口 401，注销功能失效，无法正确注销」
> 回归来源：R123（会话 cookie 持久化）

## 1. 问题与根因

用户点击顶栏「注销」后，浏览器仍处于已登录状态；`/login` 会被自动重定向回站点首页。

根因是 R123 为清空 moon-well token 引入的 `flask_session.clear()` 与
`cw_login.logout_user()` 的执行顺序冲突：

1. `logout_user()` 不直接删除 `remember_token`，而是在 session 写入
   `_remember="clear"`，由 `LoginManager._update_remember_cookie()` 在
   `after_request` 中删除 cookie；
2. 紧随其后的 `flask_session.clear()` 把这个 `_remember` 标记一并清掉；
3. 响应对空会话删除 session cookie，但 `remember_token` 原样留在浏览器
   （OIDC 登录固定 `login_user(user, remember=True)`，cookie 有效期最长 365 天）；
4. 下一次请求（注销后的 302 → `/login`）没有 `_user_id`，`_load_user()` 便从
   `remember_token` 恢复用户并 `confirm_login()`，`web.login` 见已登录直接
   302 回首页——表现为「注销无效」。

## 2. 修法

`cps/web.py::logout()` 调整为「先 `flask_session.clear()`，再 `logout_user()`」：

- clear 仍保证 moonwell access/refresh token 不滞留在 30 天滑动会话中（R123 原意不变）；
- 之后执行的 `logout_user()` 重新写入 `_remember="clear"`，`after_request` 正常
  删除 `remember_token`；
- 顺序调整不影响 `ub.delete_user_session()`（已在前一步用 `_id` 删除服务端会话记录）。

## 3. 影响面

- 仅影响 `/logout` 的会话清理顺序；登录、OIDC 回调、moon-well token 交换均不改。
- 统一账号中心（`account.haoshenqi.top`）的 SSO 会话不由本站注销；注销后再次点击
  「Log in」仍可能被 Authentik 静默授权。若产品要求「注销同时退出统一账号中心」，
  需另立需求接 RP-initiated logout（`end_session_endpoint` + `id_token_hint`）。

## 4. 验证

- 回归测试：`tests/test_session_permanent.py::test_logout_clears_moonwell_tokens`
  ——登录时带 `remember_me`，断言注销响应删除 `remember_token`、后续 `GET /login`
  返回 200（不被 remember cookie 自动登回）。
- 定向回归：`tests/test_session_permanent.py`、`test_oidc.py`、
  `test_oidc_admin_role.py`、`test_login_invite_link.py`、`test_oidc_signup.py`。
