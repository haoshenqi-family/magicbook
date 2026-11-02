# 会话注销（L3）

> 归属：admin / 登录管理 · 涉及代码：`cps/web.py::logout`、`cps/cw_login/`

## 实现方式

`GET /logout` 依次执行：

1. `ub.delete_user_session(user_id, _id)`：删除服务端 `user_session` 记录；
2. `flask_session.clear()`：清空会话内 moon-well access/refresh token 等全部键；
3. `logout_user()`：写入 `_remember="clear"`，由 `after_request` 删除 `remember_token`；
4. 重定向到 `/login`（匿名浏览开启时回 `next` 指定的站内页）。

顺序不能颠倒：`flask_session.clear()` 必须早于 `logout_user()`。反过来会把
`_remember="clear"` 标记清掉，`remember_token` 留在浏览器，下一次请求自动恢复登录
（R255 回归）。

## 边界条件

- OIDC 登录使用 `login_user(..., remember=True)`，因此每个登录用户都可能持有
  `remember_token`；注销必须同时清 session 与 remember 两个 cookie。
- 本站注销只结束 magicbook 会话，**不会**结束统一账号中心
  `account.haoshenqi.top` 的 SSO 会话；再次点击登录可能被静默授权。
- `config_anonbrowse=1` 时注销后允许回到原页面，但身份降为游客。
- 回归守卫：`tests/test_session_permanent.py::test_logout_clears_moonwell_tokens`
  覆盖 remember cookie 删除与「注销后不再自动登录」。
