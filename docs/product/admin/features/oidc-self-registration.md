# OIDC 自助注册与角色授予（L3）

> R211（2026-10-23）建立。缺陷背景与修复清单见 [lld.md](../../../project/iterations/1.0/r211-oidc-admin-role/lld.md)。
> 相关：L1 [`admin.md`](../readme/admin.md)、工作流 [`oidc-login.md`](../../kb/instructions/workflows/oidc-login.md)。

## 实现方式

建号只有一个入口：`cps/oidc.py` 的 `callback()`。决策拆成三个函数，均在 `cps/oidc.py` 模块级：

| 函数 | 职责 |
| --- | --- |
| `parse_admin_emails(raw=None)` | 解析 `OIDC_ADMIN_EMAILS`（逗号分隔，`strip().lower()`，忽略空项）；`raw=None` 时读环境变量 |
| `site_default_role()` | 读站点「新用户默认角色」`config.config_default_role`；配置未初始化（`None`）时返回 `0`（普通读者）。**函数内延迟导入 `config`**，规避 `cps/__init__` 的循环导入 |
| `resolve_new_user_role(email, admin_emails=None, default_role=None)` | 白名单命中 → `constants.ADMIN_USER_ROLES`；否则 → 站点默认角色 |

`callback()` 里三处身份路径的处理差异是本次修复的核心：

1. **OIDC subject 命中**（老用户再次登录）→ 直接登录，**不动 role**。
2. **email 精确命中既有本地账号**（存量 Calibre-Web 账号首次走 OIDC）→ 只补 `oidc_issuer` / `oidc_subject`，**保留其本地角色与书库权限**。
3. **都没命中**（自助注册新账号）→ `role=resolve_new_user_role(email)`，即 `ADMIN_USER_ROLES` **只可能来自白名单**。

`ROLE_ADMIN` 的授予因此有三个显式来源：白名单 env、管理后台手工改用户角色、`create_admin_user()` 的初始 admin 账号。除此之外没有隐式提权路径。

## 边界条件

- **邮箱为空**（Authentik 未返回 `email` claim）：不命中白名单，按默认角色建号；空串不会匹配空项白名单（`parse_admin_emails` 已剔除空项）。
- **白名单是「建号时」判据，不是持续授权**：账号一旦建好，后续把邮箱加进/移出 `OIDC_ADMIN_EMAILS` 都不会改变其角色——改角色请走管理后台或排查脚本。
- **站点默认角色若被人为配成含 `ROLE_ADMIN`**：`resolve_new_user_role` 只写 warning 日志、不静默提权也不擅自改写管理员的配置；排查脚本在降级目标角色含管理员位时直接拒绝执行。
- **`name` 唯一约束**：两个不同 subject 使用同一 `preferred_username` 时建号会命中 `user.name` 唯一约束（既有行为，本次未改）。故障表现为 OIDC 回调 500，不是角色问题。
- **存量超管不会自动降级**：本次修复只影响新建账号。存量排查用 `scripts/oidc_admin_audit.py`（默认 dry-run，见下）。
- **降级后登录态**：脚本只改 `user.role`，不碰 `oidc_issuer` / `oidc_subject` / `user_session`，因此已登录用户无需重登，权限在下一次请求即按新角色判定。

## 存量排查 / 降级 CLI

`scripts/oidc_admin_audit.py`（stdlib only，只读 SQLite 的 `user` / `settings` 两张表，不启动 Flask）：

```bash
python3 scripts/oidc_admin_audit.py                    # 只读：管理员清单（标注是否经 OIDC 登录）
python3 scripts/oidc_admin_audit.py --json /tmp/a.json # 另导出 JSON 供复核
python3 scripts/oidc_admin_audit.py --demote --ids 4,7 # 点名降级
python3 scripts/oidc_admin_audit.py --demote --emails a@b.com
```

安全边界：默认 dry-run；`--demote` 必须显式点名，**不支持全量**；写库前自动备份 `<db>.r211-bak-<时间戳>`；白名单账号即便被点名也跳过。库路径优先级：`--db` > `CONFIG_PATH/app.db` > 仓库根 `app.db`（容器内即 `/config/app.db`，需 `-v` 挂载或用 `docker exec`）。

守卫测试：`tests/test_oidc_admin_role.py`（16 条）——决策函数 7 条、回调形制 2 条、CLI 7 条；反向变异（把建号改回 `ADMIN_USER_ROLES`）实测报红。
