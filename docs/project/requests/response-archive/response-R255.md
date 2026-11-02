## 2026-10-29（R255：注销后 remember_token 未清除，用户被自动登回）

### R255（用户 sunny：「接口401 注销功能失效，无法正确注销」；补充：「资料与身份可以正常显示用户名和邮箱 authentik 正常登录」）

- **结论先行**：注销链路确实失效，但根因不是 Authentik、不是账号资料，也不在 moon-well；是本站 R123 会话持久化改动引入的 cookie 清理顺序回归。
- **复现路径**：OIDC 登录（`login_user(user, remember=True)`）→ 点击顶栏「注销」→ 到 `/login` 后被自动 302 回首页，仍是原账号。服务端会话记录已删、session cookie 已删，所以从接口看会伴随一次 401；但 `remember_token` 没删，下一次请求立刻把用户登回来。
- **根因**：`cps/web.py::logout()` 先 `logout_user()` 再 `flask_session.clear()`。`cw_login.logout_user()` 靠 session 里的 `_remember="clear"` 通知 `after_request` 删除 `remember_token`，而 `clear()` 把这个标记一起清掉了；cookie 仍在，`_load_user()` 从 remember cookie 恢复用户并 `confirm_login()`。
- **修复**：调整顺序为「删除服务端 user_session → `flask_session.clear()` → `logout_user()`」。moonwell access/refresh token 仍被清空，R123 的安全目标不变；`logout_user()` 重新写入 clear 标记，`remember_token` 随响应删除。
- **测试**：`tests/test_session_permanent.py` 的登录 fixture 改为带 `remember_me`，新增断言：注销响应必须删除 `remember_token`、后续 `GET /login` 必须 200 而不是 302。修复前红灯（`remember_del == []`），修复后 4 passed；再跑 OIDC 相关 `test_oidc.py`、`test_oidc_admin_role.py`、`test_login_invite_link.py`、`test_oidc_signup.py` 共 52 passed / 0 failed。
- **文档四问**：能力 → 无变化（恢复「注销能退出」的既定能力）；契约 → 无变化；实现/边界 → 新建 L3 `docs/product/admin/features/session-logout.md`；本次实现 → `docs/project/iterations/1.0/r255-logout-remember/lld.md`。
- **边界（需拍板）**：本站注销只结束 magicbook 会话，不结束 `account.haoshenqi.top` 的 SSO 会话；注销后若再点「Log in」，Authentik 仍会静默授权。若用户期望「注销 = 连统一账号中心一起退出」，需要另立需求做 RP-initiated logout（`end_session_endpoint` + `id_token_hint`），这会影响四个应用，不能夹在本次缺陷修复里擅自改。
- **上线**：merge/push `81356579` 已进 `origin/develop`；fnOS 镜像 `house.build-sha=81356579e064a820238ef41fbe9eabd3698c04e3`，容器 `running/healthy`（2026-10-29T23:25:23+08:00）；容器内 `/app/cps/web.py` 已确认是新顺序。
- **状态与驻留**：已上线待验收。worktree `../magicbook-r255-logout-remember`（分支 `fix/r255-logout-remember`）按闸门保留；验收通过后再删除。
- **窗口与总结**：写入前 10 节，新增后 11 节；按「写入即检查」把最旧 R245 整节原样搬至 `response-archive/response-R245.md` 并登记索引，窗口恢复 10。requests.md 条目 255 已从占位回填；冲突记录：无撞号。

