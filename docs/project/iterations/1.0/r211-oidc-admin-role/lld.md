# LLD — R211 [缺陷] OIDC 自助注册默认授予管理员权限

> 状态：**已上线并验收通过**（2026-10-23；代码 `57101027` 已 push 上线；真机端到端判据全绿——新账号 `role=0`、`/admin/view` 403、无管理入口，手动赋管理员后 200 且角色不被登录覆盖。同日按用户口径「默认都是普通用户，管理员由我手动赋予」定稿——原邮箱白名单方案已撤除）
> 迭代：1.0 · PJM 工作项 [MB-10](https://haoshenqi.pingcode.com/pjm/workitems/ldCa0y89)（缺陷，原编号 MAGICBOOK-10）· Ship 关联需求 MAGICBOOK-218
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
| 1 | 新增 `site_default_role()` / `resolve_new_user_role()`；建号改用后者 | `cps/oidc.py` |
| 2 | **不设任何自动提权开关**：角色＝站点默认角色，且强制剔除 `ROLE_ADMIN` 位；管理员只由人在管理后台手动赋予（2026-10-23 用户拍板） | `cps/oidc.py` + `.env.example`（说明性注释） |
| 3 | 存量排查 / 降级 CLI：默认 dry-run、必须点名、降级目标剔除管理员位、写库前备份 | `scripts/oidc_admin_audit.py` |
| 4 | 守卫测试：决策函数 + 回调形制 + CLI | `tests/test_oidc_admin_role.py` |

决策口径（定稿）：**新账号一律等于站点默认角色且不含管理员位**。`site_default_role()` 在配置未初始化时按 `0` 兜底，并在默认角色含管理员位时剔除该位 + 写 warning——配置项不能用来绕过「管理员手动赋予」。

三条身份路径的角色处理差异（这是「不误伤存量」的关键）：

- subject 命中 → 直接登录，不改 role；
- email 命中既有本地账号 → 只补 OIDC 绑定，保留本地角色；
- 都不命中 → 新账号按上述口径建号（唯一写 role 的分支）。

## 3. 验收（AC）

1. 新账号走 OIDC 首登后**无管理入口**，直接访问 `/admin` 返回 403；
2. 站点默认角色即便被勾上管理员位，新账号仍不是管理员（`site_default_role` 剔除）；
3. 手动在管理后台赋予管理员的账号，再次 OIDC 登录仍保持管理员（subject / email 命中路径不写 role）；
4. `scripts/oidc_admin_audit.py` 只读模式能导出清单；`--demote --ids` 降级后该账号登录态不失效、权限按新角色生效；
5. `tests/test_oidc_admin_role.py` 16 条全绿，反向变异（建号改回 `ADMIN_USER_ROLES`）报红。

## 4. 上线前必须做的运维动作

- **无需新增 env**（原 `OIDC_ADMIN_EMAILS` 白名单方案已按用户口径撤除，`.env` 不必改）。
- **存量超管排查**（容器内库为 `/config/app.db`）：

  ```bash
  docker exec magicbook python3 /app/scripts/oidc_admin_audit.py
  # 或宿主：python3 scripts/oidc_admin_audit.py --db /vol1/1000/app/magicbook/config/app.db
  ```

  按清单确认哪些是自助注册的历史账号，再 `--demote --ids ...`（自动备份到 `app.db.r211-bak-<ts>`）。降级后需要保留管理员权限的账号，在管理后台「用户管理」手动勾回。
- **新环境/新账号**：首次登录后到「用户管理」手动把站长账号设为管理员。

## 5. 风险与回滚

- 风险：站长若用一个全新账号首登，会先拿到普通用户、进不了管理后台——需已有管理员账号或直接改库赋权。这是「管理员手动赋予」口径的必然代价，已在 L1/L3 写明。
- 风险：降级误伤——脚本只处理显式点名的 id/邮箱，且写库前整库备份。
- 回滚：代码 revert 本轮 commit 即恢复旧行为（不建议，会把缺陷放回）；数据回滚用 `app.db.r211-bak-*` 覆盖。

## 6. 测试与证据

```bash
TMPDIR=$PWD/.pytest-tmp ../magicbook/.venv/bin/python -m pytest \
    tests/test_oidc_admin_role.py tests/test_oidc.py tests/test_login_invite_link.py -q
# 16 + 10 条全绿
```

反向变异：把 `cps/oidc.py` 建号改回 `role=constants.ADMIN_USER_ROLES`，`test_建号处不再直写管理员角色` 立即报红（实测）。
