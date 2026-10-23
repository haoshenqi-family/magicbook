# LLD — R211 [缺陷] OIDC 自助注册默认授予管理员权限

> 状态：开发中（2026-10-23 本轮交付，待真机验收）
> 迭代：1.0 · PJM 工作项 [MAGICBOOK-10](https://haoshenqi.pingcode.com/pjm/workitems/ldCa0y89)（缺陷）· Ship 关联需求 MAGICBOOK-218
> 来源：首访体验报告 §二 `docs/project/qa/2026-10-23/2026-10-23-qa-report.md`（截图 `e7-admin.png`）

## 1. 问题与根因

公开邀请链接注册的新账号首次登录即拥有全站管理员权限。

根因是两处常量叠加而非配置失误：

- `cps/oidc.py:138`（旧）新建账号写死 `role=constants.ADMIN_USER_ROLES`；
- `cps/constants.py:122` 该常量 = `sum(ALL_ROLES.values()) & ~ROLE_ANONYMOUS`，**含 `ROLE_ADMIN`**。

即任何走到「新账号」分支的 OIDC 登录都是超管，与站点「新用户默认角色」配置无关；同一处建号也不写 `locale`（归 R212 处理，本例不动）。

## 2. 修法

| # | 改动 | 文件 |
| --- | --- | --- |
| 1 | 新增 `parse_admin_emails` / `site_default_role` / `resolve_new_user_role`；建号改用 `resolve_new_user_role(email)` | `cps/oidc.py` |
| 2 | 管理员邮箱白名单 env `OIDC_ADMIN_EMAILS`（逗号分隔、大小写不敏感） | `cps/oidc.py` + `.env.example` |
| 3 | 存量排查 / 降级 CLI，默认 dry-run、必须点名、写库前备份 | `scripts/oidc_admin_audit.py` |
| 4 | 守卫测试：决策函数 + 回调形制 + CLI | `tests/test_oidc_admin_role.py` |

决策口径：**白名单命中 → 管理员全权限；否则 → 站点默认角色**（`config_default_role`，生产当前为 `0`＝普通读者）。`site_default_role()` 在配置未初始化时按 `0` 兜底，避免 `role=None` 让权限判断崩掉。

三条身份路径的角色处理差异（这是「不误伤存量」的关键）：

- subject 命中 → 直接登录，不改 role；
- email 命中本地账号 → 只补 OIDC 绑定，保留本地角色；
- 都不命中 → 新账号按上述决策建号。

## 3. 验收（AC）

1. 新账号走 OIDC 首登后**无管理入口**，直接访问 `/admin` 返回 403；
2. `OIDC_ADMIN_EMAILS` 命中的新账号首登仍为管理员；
3. 存量管理员账号（含 `admin@example.org`）登录后角色不变；
4. `scripts/oidc_admin_audit.py` 只读模式能导出清单；`--demote --ids` 降级后该账号登录态不失效、权限按新角色生效；
5. `tests/test_oidc_admin_role.py` 16 条全绿，反向变异（建号改回 `ADMIN_USER_ROLES`）报红。

## 4. 上线前必须做的运维动作

- **在生产 `.env` 里配 `OIDC_ADMIN_EMAILS=站长邮箱`**。不配也不会让站长掉权（站长账号已存在，走 subject / email 命中路径），但配了才能保证「以后用新邮箱注册仍是管理员」。
- **存量超管排查**（容器内库为 `/config/app.db`）：

  ```bash
  docker exec magicbook python3 /app/scripts/oidc_admin_audit.py
  # 或宿主：python3 scripts/oidc_admin_audit.py --db /vol1/1000/app/magicbook/config/app.db
  ```

  按清单确认哪些是自助注册的历史账号，再 `--demote --ids ...`（自动备份到 `app.db.r211-bak-<ts>`）。

## 5. 风险与回滚

- 风险：白名单漏配导致「新注册的站长账号」不是管理员——影响面仅限新建账号，且可用管理后台手工提权修复。
- 风险：降级误伤本地管理员——脚本只处理显式点名的 id/邮箱，且白名单账号跳过、写库前整库备份。
- 回滚：代码 revert 本轮 commit 即恢复旧行为（不建议，会把缺陷放回）；数据回滚用 `app.db.r211-bak-*` 覆盖。

## 6. 测试与证据

```bash
TMPDIR=$PWD/.pytest-tmp ../magicbook/.venv/bin/python -m pytest \
    tests/test_oidc_admin_role.py tests/test_oidc.py tests/test_login_invite_link.py -q
# 16 + 10 条全绿
```

反向变异：把 `cps/oidc.py` 建号改回 `role=constants.ADMIN_USER_ROLES`，`test_建号处不再直写管理员角色` 立即报红（实测）。
