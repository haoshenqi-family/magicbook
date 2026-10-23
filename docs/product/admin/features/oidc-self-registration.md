# OIDC 自助注册与角色授予（L3）

> R211（2026-10-23）建立；同日按用户拍板口径**定稿**——「默认都是普通用户，管理员用户由我手动赋予」。
> 缺陷背景与修复清单见 [lld.md](../../../project/iterations/1.0/r211-oidc-admin-role/lld.md)。
> 相关：L1 [`admin.md`](../readme/admin.md)、工作流 [`oidc-login.md`](../../kb/instructions/workflows/oidc-login.md)。

## 实现方式

建号只有一个入口：`cps/oidc.py` 的 `callback()`。角色决策在模块级两个函数里：

| 函数 | 职责 |
| --- | --- |
| `site_default_role()` | 读站点「新用户默认角色」`config.config_default_role`，**强制剔除 `ROLE_ADMIN` 位**；配置未初始化（`None`）时返回 `0`（普通读者）。**函数内延迟导入 `config`**，规避 `cps/__init__` 的循环导入 |
| `resolve_new_user_role()` | 无参数，直接返回 `site_default_role()`；语义即「自助注册角色＝站点默认角色，永不含管理员位」 |

**没有任何逃生开关**：不放 env 白名单、不按邮箱判断、不看 authentik 侧 claim。管理员只有两条获得路径——管理后台「用户管理」里人工改角色，以及 `create_admin_user()` 建的初始 admin 账号。

`callback()` 里三处身份路径的处理差异是本次修复的核心：

1. **OIDC subject 命中**（老用户再次登录）→ 直接登录，**不动 role**。
2. **email 精确命中既有本地账号**（存量 Calibre-Web 账号首次走 OIDC）→ 只补 `oidc_issuer` / `oidc_subject`，**保留其本地角色与书库权限**。
3. **都没命中**（自助注册新账号）→ `role=resolve_new_user_role()`。

因此「手动赋予的管理员」不会因为再次登录被覆盖：第 1、2 条路径都不写 role；第 3 条只发生在建号那一刻。

## 边界条件

- **站点默认角色被人为勾了管理员位**：`site_default_role()` 剔掉 `ROLE_ADMIN` 后返回，并写 warning 日志。即配置项不能用来绕过「管理员手动赋予」的口径；其他权限位（下载 / 上传 / 编辑等）照常尊重配置。
- **`config_default_role` 未初始化是 `None` 而非 0**：必须显式兜底为 `0`，否则 `role=None` 会让 `has_flag` / 权限判断崩。
- **邮箱为空**（Authentik 未返回 `email` claim）：与角色无关，走默认角色建号。
- **`name` 唯一约束**：两个不同 subject 使用同一 `preferred_username` 时建号会命中 `user.name` 唯一约束（既有行为，本次未改），表现为 OIDC 回调 500。
- **存量超管不会自动降级**：本次修复只影响新建账号；存量排查用 `scripts/oidc_admin_audit.py`。
- **降级后登录态**：脚本只改 `user.role`，不碰 `oidc_issuer` / `oidc_subject` / `user_session`，已登录用户无需重登，权限在下一次请求按新角色判定。

## 存量排查 / 降级 CLI

`scripts/oidc_admin_audit.py`（stdlib only，只读 SQLite 的 `user` / `settings`，不启动 Flask）：

```bash
python3 scripts/oidc_admin_audit.py                    # 只读：管理员清单（标注是否经 OIDC 登录）
python3 scripts/oidc_admin_audit.py --json /tmp/a.json # 另导出 JSON 供复核
python3 scripts/oidc_admin_audit.py --demote --ids 4,7 # 点名降级
python3 scripts/oidc_admin_audit.py --demote --emails a@b.com
```

安全边界：默认 dry-run；`--demote` 必须显式点名，**不支持全量**；写库前自动备份 `<db>.r211-bak-<时间戳>`；**降级目标角色＝站点默认角色剔除管理员位**（脚本不会把任何人留在或推回管理员）。库路径优先级：`--db` > `CONFIG_PATH/app.db` > 仓库根 `app.db`（容器内即 `/config/app.db`，需 `-v` 挂载或用 `docker exec`）。

守卫测试：`tests/test_oidc_admin_role.py`（16 条）——决策函数 5 条、回调形制 3 条、CLI 8 条；反向变异（把建号改回 `ADMIN_USER_ROLES`）实测报红。
