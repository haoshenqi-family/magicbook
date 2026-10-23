# OIDC 自助注册与角色授予（L3）

> R211（2026-10-23）建立；同日按用户拍板口径**定稿**——「默认都是普通用户，管理员用户由我手动赋予」。
> 缺陷背景与修复清单见 [lld.md](../../../project/iterations/1.0/r211-oidc-admin-role/lld.md)。
> R217（2026-10-23）新增「注册后自动回 magicbook」——注册链路从「停在 Authentik」改为「自动回站且已是登录态」，见 [§ 注册后自动回站](#注册后自动回站r217)。
> 相关：L1 [`admin.md`](../../readme/admin.md)、工作流 [`oidc-login.md`](../../../kb/instructions/workflows/oidc-login.md)。

## 实现方式

建号只有一个入口：`cps/oidc.py` 的 `callback()`。角色决策在模块级两个函数里：

| 函数 | 职责 |
| --- | --- |
| `site_default_role()` | 读站点「新用户默认角色」`config.config_default_role`，**强制剔除 `ROLE_ADMIN` 位**；配置未初始化（`None`）时返回 `0`（普通读者）。**函数内延迟导入 `config`**，规避 `cps/__init__` 的循环导入 |
| `resolve_new_user_role()` | 无参数，直接返回 `site_default_role()`；语义即「自助注册角色＝站点默认角色，永不含管理员位」 |

**没有任何逃生开关**：不放 env 白名单、不按邮箱判断、不看 authentik 侧 claim。管理员只有两条获得路径——管理后台「用户管理」里人工改角色，以及 `create_admin_user()` 建的初始 admin 账号。

`callback()` 里三处身份路径的处理差异是本次修复的核心：

1. **OIDC subject 命中**（老用户再次登录）→ 直接登录，**不动 role**。
2. **email 精确命中既有本地账号**（存量本地账号首次走 OIDC）→ 只补 `oidc_issuer` / `oidc_subject`，**保留其本地角色与书库权限**。
3. **都没命中**（自助注册新账号）→ `role=resolve_new_user_role()`。

因此「手动赋予的管理员」不会因为再次登录被覆盖：第 1、2 条路径都不写 role；第 3 条只发生在建号那一刻。

## 注册后自动回站（R217）

> 完整设计与现网实证见 [lld.md](../../../project/iterations/1.0/r217-oidc-signup-return/lld.md)。

### 链路

R103 起登录页的「注册账号」按钮直接指向 `AUTHENTIK_ENROLLMENT_INVITE_URL`，
且 `target="_blank"` 新窗口打开。用户完成注册后停在 Authentik 侧，必须自己切回
magicbook 再点一次「Log in」——**注册与登录是断开的两步**。

R217 起改为三段式，注册完自动回站且**已是登录态**：

```
magicbook /login  「注册账号」按钮（同窗口，不再 target=_blank）
   │  GET /oidc/signup   ← magicbook 侧新端点
   │    ① authlib 生成 OIDC 授权 URL（含 state / nonce / PKCE），参数存 Flask session
   │    ② 从 AUTHENTIK_ENROLLMENT_INVITE_URL 解析出 itoken
   │    ③ 把授权 URL 的 path+query 编码成 next，拼成邀请 flow URL
   ▼
account.haoshenqi.top/if/flow/invitation-enrollment/?query=itoken%3D..&next=%2Fapplication%2Fo%2Fauthorize%2F%3F..
   │  用户填账号建号 → 末位 UserLoginStage 建立 Authentik 登录态
   ▼  flow 完成，_flow_done() 取 session 里的 next（必须是相对路径）→ 302
account.haoshenqi.top/application/o/authorize/?client_id=..&state=..&nonce=..&redirect_uri=..
   │  已登录 → 签发 code → 302
   ▼
magicbook.haoshenqi.top/oidc/callback?code=..&state=..
   │  换 token → 按 sub 绑定/新建本地用户 → login_user
   ▼
magicbook 首页（已登录）
```

### 关键实现点

| 点 | 做法 | 为什么 |
| --- | --- | --- |
| `next` 指向**同域 authorize**（`/application/o/authorize/?...`），不是 magicbook callback | Authentik 的 `_flow_done()` 硬性拒绝绝对 `next`（`is_url_absolute` 判 netloc）；authorize 与 flow 同域，可写成相对路径 | 指向 authorize 后由 Authentik 负责「已登录→签发 code→回调」，magicbook 侧 `callback()` **零改动**——建号/绑号/角色判定不分叉 |
| `state` / `nonce` / `code_verifier` 存 magicbook 的 Flask session | 复用 authlib 的 `create_authorization_url()` + `save_authorize_data()`，与既有 `/oidc/login` 路径一致 | 回调时 `authorize_access_token()` 凭 `state` 取回并校验 nonce，无需另建存储 |
| itoken 从既有 `AUTHENTIK_ENROLLMENT_INVITE_URL` **解析**，不新增 env 变量 | 解析 query 取 `itoken`（兼容 `token` key） | 避免「invite URL 与 invite token 两份配置各自漂移」，轮换仍只改一个地方 |
| 「注册完回 magicbook 哪个页面」走 `get_redirect_location(next, "web.index")` | 复用 `cps/redirect.py` 的 url_map 白名单校验 | 开放重定向防护；用户可控部分只限站内相对路径 |

### 边界条件

- **`AUTHENTIK_ENROLLMENT_INVITE_URL` 未配置** → `/oidc/signup` 不渲染入口（沿用 R103 语义），登录页无注册按钮。
- **itoken 解析不出**（URL 形态被改）→ flash 错误并回登录页，**不静默跳一个坏链接**。
- **邀请过期**（现网 invitation `expires=2026-10-30 07:10 UTC`）→ Authentik 侧报 "Invalid invite"；本条不解决过期问题（属运维轮换）。
- **用户在 flow 中途关页面** → 根本到不了 callback，无副作用；magicbook session 里会残留一条未被消费 的 state 数据（框架级过期，不影响登录）。
- **用户已有账号再点注册** → invitation flow 的 `user_write` stage 会因 username 冲突报错，这是 Authentik 侧既有语义。
- **OIDC 未启用** → `/oidc/signup` flash 错误并回登录页。

### 守卫测试

`tests/test_oidc_signup.py`（16 条）：`_invite_token` 3 条、`/oidc/signup` 9 条（302 目标 / next 为相对路径 / next 指向 `/application/o/authorize/` / next 含 client_id+redirect_uri+response_type+scope / state 与 session 一致 / 开放重定向拒绝 / 站内 next 保留 / redirect_uri 回退 / 未配置邀请不跳 / OIDC 关闭不跳）、登录页 3 条。
反向变异实测两次报红：next 不剥 scheme+host（2 条红）、next 编码保留 `&`（3 条红）。

### 现网端到端实证（2026-10-23）

用与代码同构的 URL 在现网实测完整链路，**不是推断**：

1. `GET /api/v3/flows/executor/invitation-enrollment/?query=itoken=..&next=..` → 返回 `ak-flow-redirect`，其 `to` 中的 query 完整保留了 `next`（证明 next 已进入 Authentik session 机制）。
2. 逐 stage POST（identification → user-write）完成建号 → flow 结束返回
   `{"component": "xak-flow-redirect", "to": "/application/o/authorize/?client_id=..&state=..&nonce=..&redirect_uri=.."}`
   —— **next 被精确还原为相对路径的 authorize URL**，未触发 "Invalid next URL"。
3. 跟随该 redirect → 302 到 `default-provider-authorization-explicit-consent`（provider 的授权 flow），consent 阶段的 `pending_user` 即刚注册的新用户。
4. 提交 consent → flow 结束返回
   `{"to": "https://magicbook.haoshenqi.top/oidc/callback?code=..&state=.."}`
   —— **Authentik 已签发 code 并准备回调 magicbook**。

> 实测用的测试账号已在验证后删除（Authentik 侧 `r217e2eprobe` 用户与对应 consent 记录）。

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
## 注册入口本身：链接形式是它的命门

自助注册**不是**公开入口，而是走 Authentik 的 `invitation-enrollment` flow：登录页「注册账号 Sign up (invite)」指向一条具体邀请（`.env` 的 `AUTHENTIK_ENROLLMENT_INVITE_URL`）。

**这条链接的「形式」比链接本身更要命。** 2026-10-23 实测：老式 `?itoken=<uuid>` 一律被 authentik 判 `Invalid invite/invite not found`，而邀请记录本身完全正常（`single_use=false`、未过期、Django ORM `filter_not_expired` 能查到）。根因在 authentik 源码 `authentik/flows/views/executor.py`：

```python
get_params = QueryDict(request.GET.get(QS_QUERY, ""))   # QS_QUERY = "query"
```

顶层 query 不被读，**必须整段塞进 `?query=` 里**——正确形式是 `?query=itoken%3D<uuid>`（authentik 自己回的 `to` 字段也是这个形式）。

失效的表现极具迷惑性：点进去只显示一句「Invalid invite」，**不会有人来报「注册不了」**，登录页上的注册按钮就此长期坏死而不被察觉（R161 域名切换只换域名、没动形式，入口就此报废，直到 2026-10-23 才被追出来）。

两点推论：

- **新账号一律普通用户**这条修复，正是让「谁拿到链接都无所谓」成立的前提——链接被转发也只产生普通用户，管理员仍由人工赋予。
- **入口长期可用的策略已定**（2026-10-23 用户拍板）：**邀请设为可复用**（`single_use=False`）、有效期 90 天——否则每注册一个人入口就死一次，而入口失效只表现为一句报错，很难被察觉。同时必须使用 Authentik 的嵌套 query 形式（`?query=itoken%3D<pk>`）。轮换工具（建邀请 → 改 `.env` → 重建 → 校验）： [`scripts/rotate_authentik_invite.py`](../../../../scripts/rotate_authentik_invite.py)（默认 dry-run，`--apply` 才动服务器；细节见 [OIDC 登录工作流](../../kb/instructions/workflows/oidc-login.md) §2）。
