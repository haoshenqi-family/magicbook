# LLD：注册后自动回 magicbook（R217）

> 状态：已开发，待验收
> 关联台账：R217（`docs/project/requests/requests.md` 第 217 条）
> 关联需求：MAGICBOOK-11（R212 入口层）的延伸——注册链路的落点与登录态衔接
> 相关实现说明：[`docs/product/admin/features/oidc-self-registration.md`](../../../../product/admin/features/oidc-self-registration.md)
> 工作流：[`docs/kb/instructions/workflows/oidc-login.md`](../../../../kb/instructions/workflows/oidc-login.md)

## 1. 问题

现状（R103 起）：magicbook 登录页渲染「注册账号 Sign up」按钮，指向
`.env` 的 `AUTHENTIK_ENROLLMENT_INVITE_URL`（Authentik 邀请注册 flow），且 `target="_blank"` 新窗口打开。

用户完成注册后停在 **Authentik 侧**（邀请 flow 结束 → 默认回落到 authentik 根页），
必须自己切回 magicbook 再点一次「Log in」——**注册与登录是断开的两步**，且新窗口意味着
「注册完不知道该去哪」。

目标（用户 2026-10-23 拍板「3需要做」）：**注册完成后自动回到 magicbook，且已经是登录态**，
用户不再需要第二次点击。

## 2. 机制约束（现网实证，2026-10-23 Authentik 2025.10.2）

先读源码与实测，避免凭印象设计：

| 约束 | 证据 | 影响 |
| --- | --- | --- |
| flow 结束时的 `next` **必须是相对路径** | `authentik/flows/views/executor.py` `_flow_done()`：`if next_param and not is_url_absolute(next_param)`，否则报 "Invalid next URL"（`is_url_absolute` = `urlparse(url).netloc` 非空） | `next` **不能**直接写 `https://magicbook.haoshenqi.top/oidc/callback` |
| `next` 从 session 的 `SESSION_KEY_GET` 取 | executor `dispatch()`：`request.session[SESSION_KEY_GET] = get_params`，`get_params = QueryDict(request.GET.get("query", ""))`；前端 `ak-flow-executor` 用 `window.location.search.substring(1)` 整段透传 | `next` 必须出现在**浏览器地址栏的 query**里，才能随 flow 全程存活 |
| flow 完成前会自动建立 Authentik 登录态 | `invitation-enrollment` 末位 stage 是 `invite-enroll-user-login`（`UserLoginStage` → `django.contrib.auth.login()`） | flow 结束后用户已是 Authentik 用户，可直接授权 |
| OIDC authorize 端点与 flow **同域** | discovery：`authorization_endpoint = https://account.haoshenqi.top/application/o/authorize/` | `next` 可以写成**同域相对路径** `/application/o/authorize/?...` —— 这正好绕开「必须相对路径」的约束 |
| authorize 未登录时跳默认认证 flow | 实测 302 → `/flows/-/default/authentication/?next=/application/o/authorize/%3F...` | `next` 指向 authorize 时，若用户尚未登录会要求再登录——但 flow 末位已建会话，故不会发生 |
| `next` 可携带 query | `redirect_with_qs(next_param)` → `reverse()` 失败则 `redirect(view)`，Django `resolve_url` 对 `/path?query` 原样使用 | `next=/application/o/authorize/?client_id=..&state=..&redirect_uri=..` 可行 |

## 3. 方案

### 3.1 链路

```
magicbook /login  「注册账号」按钮
   │  （不再 target=_blank，改为同窗口跳转）
   ▼
GET /oidc/signup          ← 新端点（magicbook 侧）
   │  1. 用 authlib 生成 OIDC 授权 URL（含 state / nonce / PKCE）
   │  2. state 等参数存 magicbook 的 Flask session
   │  3. 把授权 URL 的 path+query 编码为 next
   │  4. 拼上 Authentik 邀请 flow 的 itoken
   ▼
account.haoshenqi.top/if/flow/invitation-enrollment/?itoken=..&next=%2Fapplication%2Fo%2Fauthorize%2F%3F..
   │  用户填账号 → 建号 → UserLoginStage 建立 Authentik 登录态
   ▼  flow 完成，_flow_done() 取 session 里的 next（相对路径）→ 302
account.haoshenqi.top/application/o/authorize/?client_id=..&state=..&redirect_uri=..&nonce=..
   │  已登录 → 静默签发 code → 302
   ▼
magicbook.haoshenqi.top/oidc/callback?code=..&state=..
   │  换 token → 按 sub 绑定/新建本地用户 → login_user
   ▼
magicbook 首页（已登录）
```

### 3.2 关键设计点

**为什么 `next` 指向同域 authorize 而不是 magicbook callback**：Authentik 硬性拒绝绝对 `next`。
指向 authorize 后，Authentik 负责「已登录 → 签发 code → 回调 magicbook」，
magicbook 侧 `callback()` 逻辑完全复用，无需改动——**建号/绑号/角色判定一条路径，不分叉**。

**state 的存放**：`/oidc/signup` 用 authlib 的 `create_authorization_url()` 生成
`state` / `nonce` / `code_verifier`，写入 Flask session（`framework.set_state_data`），
与既有 `/oidc/login` 路径完全一致——`callback()` 里 `authorize_access_token()`
凭 `state` 取回 session 数据、校验 nonce，**零改动**。

**PKCE**：`create_authorization_url` 在 `client.code_challenge_method` 存在时自动带
`code_challenge`；`code_verifier` 随 state 存 session，回调时由 authlib 自动带上。

**itoken 从哪来**：`AUTHENTIK_ENROLLMENT_INVITE_URL` 现有形态是
`https://account.haoshenqi.top/if/flow/invitation-enrollment/?itoken=<uuid>`。
新增 `AUTHENTIK_ENROLLMENT_INVITE_TOKEN`（纯 uuid）更干净，但为避免**双份配置漂移**，
本次**从既有 URL 里解析 itoken**，不新增 env 变量——轮换仍只改一个地方。

**防开放重定向**：`next` 的 path 固定取自 authlib 生成的
`authorization_endpoint`（来自 discovery 文档），**不接受外部输入**；
magicbook 侧 `redirect_uri` 取既有 `AUTHENTIK_MAGICBOOK_REDIRECT_URI` 或 `url_for` 回退。
用户可控的只有「注册完成后回到 magicbook 的哪个页面」（`next` 参数，走
`get_redirect_location` 同款白名单校验）。

### 3.3 变更点

| 文件 | 变更 |
| --- | --- |
| `cps/oidc.py` | 新增 `GET /oidc/signup`：生成授权 URL → 拼 invitation flow URL（带 `next`）→ 302 |
| `cps/oidc.py` | 新增 `GET /oidc/signup`：从 `AUTHENTIK_ENROLLMENT_INVITE_URL` 解析 itoken |
| `cps/web.py` | 登录页注入 `authentik_signup_url`（指向 `/oidc/signup`），保留 `authentik_invite_url` 兜底 |
| `cps/templates/login.html` | 「注册账号」按钮改为指向 `/oidc/signup`，去掉 `target="_blank`（同窗口连续体验） |
| `tests/test_oidc_signup.py` | 新增守卫测试 |

### 3.4 边界条件

- **`AUTHENTIK_ENROLLMENT_INVITE_URL` 未配置** → `/oidc/signup` 不渲染入口（沿用 R103 语义），
  登录页不出现注册按钮。
- **itoken 解析不出**（URL 形态被改）→ flash 错误并回登录页，**不静默跳一个坏链接**。
- **OIDC 未配置**（`AUTHENTIK_OIDC_ENABLED` 为假）→ flash 错误并回登录页。
- **邀请过期**（现网 invitation `expires=2026-10-30 07:10 UTC`）→ Authentik 侧报
  "Invalid invite"；本条不解决过期问题（属运维轮换，另行处理），
  但**错误提示必须能让用户看懂**，不能白屏。
- **用户在 flow 中途关页面** → 回到 magicbook 时 `session` 里没有对应 state，
  `callback()` 不会被触发（因为根本没到 callback），无副作用。
- **用户已有账号再点注册** → invitation flow 的 `user_write` stage 会因 username 冲突报错，
  这是 Authentik 侧既有语义，本条不改。
- **`next` 参数里含用户可控的「回站页面」** → 必须做开放重定向校验（只允许站内相对路径）。

## 4. 测试

### 4.1 守卫测试

`tests/test_oidc_signup.py`（16 条）：

1. `/oidc/signup` 返回 302，`Location` 指向 invitation-enrollment flow 且含 `next`。
2. `next` 解码后是**相对路径**且指向 `/application/o/authorize/`（守住 Authentik 的硬约束）。
3. `next` 内的 `state` 与写进 session 的一致（回调能取回）。
4. `next` 内含正确的 `client_id` 与 `redirect_uri`。
5. `AUTHENTIK_ENROLLMENT_INVITE_URL` 未配置时，`/login` 不渲染注册入口。
6. 登录页注册按钮指向 `/oidc/signup` 且**不再** `target="_blank"`。
7. `next` 传外部绝对 URL 时被拒（开放重定向防护）。
8. 反向变异：把 `next` 改成绝对 URL → 测试报红。

`_invite_token` 另 3 条（`itoken` / `token` 两种 key、无 env 返回 None）。
`/oidc/signup` 另 9 条（302 目标、next 相对路径、next 指向 authorize、
next 含 client_id+redirect_uri+response_type+scope、state 与 session 一致、
开放重定向拒绝、站内 next 保留、redirect_uri 回退、未配置邀请不跳、OIDC 关闭不跳）。

**实测结果**（2026-10-23，`tests/test_oidc_signup.py` + `tests/test_oidc.py` +
`tests/test_login_invite_link.py` + `tests/test_oidc_admin_role.py` +
`tests/test_smoke.py` + `tests/test_i18n_seed_contract.py`）：
**49 passed / 0 failed**。

**反向变异**（两次，均实测报红）：

| 变异 | 报红用例数 |
| --- | --- |
| `next` 不剥 scheme+host（写成绝对 URL） | 2（`test_next_is_relative_path` / `test_next_points_to_authorize_endpoint`） |
| `next` 编码保留 `&`（`quote(target, safe="&")`） | 3 |

> 注：第一次变异用 `quote(target, safe="/")` 无效——`quote` 默认 `safe="/"` 已编码 `&`，两次变异等价，测试当然不红。**变异必须真的改坏语义**，否则"守卫生效"是假象。

### 4.2 现网端到端实证

仅靠单测不足以证明「Authentik 真会这样跳」——故用**与代码同构的 URL** 在现网
（`account.haoshenqi.top`，Authentik 2025.10.2）实测完整链路：

| 步 | 操作 | 实测响应 | 结论 |
| --- | --- | --- | --- |
| 1 | `GET /api/v3/flows/executor/invitation-enrollment/?query=itoken=..&next=..` | `{"component":"xak-flow-redirect","to":"...&query=itoken%3D..%26next%3D%252Fapplication%252Fo%252Fauthorize%252F%253Fclient_id%253D.."}` | `next` 已进入 Authentik session 机制（`SESSION_KEY_GET`），双重编码保留 |
| 2 | 对照组：同样请求但**不带** `next` | 同样返回 `ak-flow-redirect` | 确认 `ak-flow-redirect` 是**正常首阶段跳转**，不是错误响应 |
| 3 | 跟随 redirect 取 stage → 逐 stage POST（identification → user-write）建号 | 建号成功；flow 结束时返回 `{"component":"xak-flow-redirect","to":"/application/o/authorize/?client_id=..&response_type=code&scope=openid+profile+email&state=..&nonce=..&redirect_uri=https%3A%2F%2Fmagicbook.haoshenqi.top%2Foidc%2Fcallback"}` | **`next` 被精确还原为相对路径的 authorize URL**，未触发 "Invalid next URL"；`&` 未被提前截断（编码正确） |
| 4 | 跟随该 redirect | `302 → /if/flow/default-provider-authorization-explicit-consent/?client_id=..` | provider 的授权 flow 是 `default-provider-authorization-explicit-consent`；consent 阶段 `pending_user` 正是刚注册的新用户 |
| 5 | 提交 consent | flow 结束返回 `{"component":"xak-flow-redirect","to":"https://magicbook.haoshenqi.top/oidc/callback?code=..&state=.."}` | **Authentik 已签发 code 并准备回调 magicbook**——链路终点达成 |

> 实测用的测试账号（`r217e2eprobe`）与对应 consent 记录已在验证后从 Authentik 删除。

**踩过的坑（如实记）**：

- Authentik executor 的 POST 需 CSRF：header 名是 **`X-authentik-csrf`**
  （`CSRF_HEADER_NAME = "HTTP_X_AUTHENTIK_CSRF"`，Django 把 `HTTP_X_…` 映射回 `X-…`），
  **不是**常见的 `X-CSRFToken`；且必须同时带 `Referer`。取 cookie 值用
  `awk '/authentik_csrf/{print $NF}'`——本机 `grep` 不支持 `-P`。
- 本机 `pytest` 并发跑同一 `TMPDIR` 会撞 `EEXIST: mkdir …/pytest-of-root`，
  报 4 个 ERROR（**与被测代码无关**，是 tmpdir 竞争）。改用独立 `TMPDIR` 后 49 条全绿。

## 5. 部署

代码上线（push develop → fnOS 自动构建部署）后，**无需改 Authentik 配置**——
`next` 机制与 user-login stage 都是 Authentik 既有能力。

验收步骤：

1. 打开 `https://magicbook.haoshenqi.top/login`，点「注册账号」。
2. 走完邀请注册（建号）。
3. **判据**：浏览器自动落到 `magicbook.haoshenqi.top/oidc/callback?code=..` 并回到首页，
   右上角显示已登录用户；**不需要**再点一次「Log in」。

> 注意：magicbook provider 的授权 flow 是 `default-provider-authorization-explicit-consent`，
> 新用户首次授权会看到一个 consent 确认页（「即将登录 magicbook」）——这是 Authentik 的
> 授权确认环节，与「注册→回站」链路本身无关（老用户授权记录 30 天内免重复确认）。
> 若希望完全无感，需把 provider 的授权 flow 改为 `default-provider-authorization-implicit-consent`——
> 属现网配置调整，**不在本条范围**，待用户拍板。

## 6. 不做

- 不改 `callback()` 的建号/角色逻辑（R211 已定稿，一并复用）。
- 不新增 env 变量（itoken 从既有 URL 解析）。
- 不解决 invitation 过期问题（运维轮换，另行处理）。
- 不改 moon-well / note / immich 的任何配置。
- 不改 Authentik provider 的 consent 模式（见 §5 备注）。
