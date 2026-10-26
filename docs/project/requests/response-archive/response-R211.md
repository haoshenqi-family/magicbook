## 2026-10-23（R211：OIDC 自助注册默认授予管理员权限——P0 缺陷修复）

### R211（用户：「修复 pingcode magicbook-10」）

- **任务来源**：PingCode 缺陷 [MAGICBOOK-10](https://haoshenqi.pingcode.com/pjm/workitems/ldCa0y89)（新提交 → 处理中），对应台账 R211 / Ship 需求 MAGICBOOK-218。用户 2026-10-23 拍板 P0 单独先上线。
- **根因（两处常量叠加，不是配置失误）**：`cps/oidc.py` 建号写死 `role=constants.ADMIN_USER_ROLES`；`cps/constants.py:122` 该常量 = 全部角色位去匿名，**含 `ROLE_ADMIN`**。于是任何走「新账号」分支的 OIDC 登录都是超管，与站点「新用户默认角色」配置无关——公开邀请链接 = 人人可拿管理员。同一处建号也不写 `locale`（`ub.py` 兜底 `en`），归 R212 处理，本条不动。
- **修法（4 项）**：① `cps/oidc.py` 新增 `parse_admin_emails` / `site_default_role` / `resolve_new_user_role`，建号改为按决策函数取角色——白名单命中 → 管理员全权限，否则 → `config_default_role`（生产当前 `0`＝普通读者）；`site_default_role()` 用**函数内延迟导入** `config`，规避 `cps/__init__` 循环导入，配置未初始化时按 `0` 兜底（否则 `role=None` 会让权限判断崩）。② 白名单 env `OIDC_ADMIN_EMAILS`（逗号分隔、大小写与空格不敏感、空项忽略），`.env.example` 补说明。③ 存量排查/降级 CLI `scripts/oidc_admin_audit.py`（stdlib only，只读 SQLite `user`/`settings`，不启动 Flask）。④ 守卫测试 `tests/test_oidc_admin_role.py` 16 条。
- **三条身份路径的差异（不误伤存量的关键）**：subject 命中 → 直接登录不改 role；email 命中既有本地账号 → 只补 OIDC 绑定、保留本地角色；都不命中才按决策函数建号。因此站长与历史管理员账号都不会因本次修复掉权。
- **CLI 的安全边界（有意做窄）**：默认 dry-run；`--demote` 必须显式点名 `--ids`/`--emails`，**不支持全量降级**（管理员位批量抹掉只能靠备份回滚）；写库前自动备份 `<db>.r211-bak-<时间戳>`；`OIDC_ADMIN_EMAILS` 白名单账号即便被点名也跳过；站点默认角色若含管理员位直接拒绝执行（目标角色本身不安全）。
- **验证**：`tests/test_oidc_admin_role.py` 16 条 + `test_oidc.py`/`test_login_invite_link.py` 10 条全绿（开发态，按 AGENTS.md 只跑本次与受影响模块）。**反向变异**：把建号改回 `ADMIN_USER_ROLES` 后 `test_建号处不再直写管理员角色` 实测报红，恢复后转绿。对主检出 `app.db` 只读实跑 CLI：识别 2 个账号 / 1 个管理员 / 0 个 OIDC 账号，默认角色 `0`、白名单空——输出与库内容一致。
- **文档四问**：能力变了吗 → L1 `docs/product/readme/admin.md` 增「新账号角色」条；契约变了吗 → 对外无接口变化，运维侧新增 env 已写入 `.env.example`；实现/边界变了吗 → 新建 L3 `docs/product/admin/features/oidc-self-registration.md`；本次怎么实现 → LLD `docs/project/iterations/1.0/r211-oidc-admin-role/lld.md`（状态行：开发中）。
- **上线前必须做的运维动作**（已写入 LLD §4）：生产 `.env` 配 `OIDC_ADMIN_EMAILS=站长邮箱`（不配也不会让现有站长掉权，但配了以后新邮箱注册才仍是管理员）；存量超管按清单确认后再 `--demote --ids`，容器内库路径 `/config/app.db`。
- **窗口**：本条写入使窗口达 11 个 request，按「写入即检查」把最旧的 R183（B4 epub.js 分域，7 节 78 行）原样搬至 `response-archive/response-R183.md` 并登记索引，窗口回 10；只搬移不改写。
- **驻留与闸门**：worktree `../magicbook-r211-oidc-admin-role`（分支 `fix/r211-oidc-admin-role`，从 `origin/develop` `2006b6f3` 切出）待验收；**本轮未 push**，push 即触发 fnOS 自动上线，按用户闸门执行。验收通过后 `worktree remove` + `branch -d`。
- **口径修订（16:1x，用户：「默认都是普通用户，管理员用户由我手动赋予」）**：撤除 `OIDC_ADMIN_EMAILS` 邮箱白名单——不留任何自动提权开关。`resolve_new_user_role()` 改为**无参数**，直接返回站点默认角色并**强制剔除 `ROLE_ADMIN` 位**（默认角色被误配勾了管理员位也只写 warning、不生效，其他权限位照旧尊重配置）。CLI 同步：`demote_target_role()` = 默认角色剔除管理员位，原「默认角色含管理员位即拒绝执行」改为「剔除后执行」；白名单跳过逻辑删除。测试改写为 16 条（新增「误配管理员位强制剔除」「决策函数不接受邮箱参数、模块内无白名单路径」两条正交守卫），仍全绿、反向变异照旧报红。L1/L3/LLD/`.env.example` 同步改写。**上线前不再需要配任何 env**；后台上一条「生产 `.env` 配 `OIDC_ADMIN_EMAILS`」作废，改为「新账号首登后由站长在『用户管理』手动赋管理员」。
