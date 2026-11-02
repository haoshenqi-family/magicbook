# Overview：Authentik OIDC 登录说明

> 功能路径：`/oidc/login` → Authentik 授权 → `/oidc/callback`
> 注册路径（R217）：`/oidc/signup` → 邀请注册 flow →（静默授权）→ `/oidc/callback`
> 相关代码：`cps/oidc.py`
> 适用版本：magicbook（Calibre-Web fork，Python/Flask + Gevent，生产端口 **8083**（fnOS）；8085 系 Ubuntu 开发机 UBT 旧部署，已停用待清理）

## 1. 功能概述

magicbook 以 **Authentik** 作为统一身份源（IdP），用户可从登录页经
OIDC（OpenID Connect）授权码模式登录：

```
用户访问 /oidc/login                         （登录页「Authentik 登录」按钮）
   │  302 跳转到 Authentik 授权页
   ▼
https://account.haoshenqi.top/application/o/authorize/?
    client_id=...&redirect_uri=<回调>&scope=openid+profile+email&...
   │  用户确认后 Authentik 回调
   ▼
/oidc/callback?code=...&state=...
   │  用 client_secret 换 token → 校验 id_token → 按 sub 绑定/新建本地用户
   ▼
登录成功，跳转回 next 页面
```

- 用户首次登录：按 `preferred_username`/`email` 自动创建本地账号，并以
  Authentik `sub` 作为 `oidc_subject` / `user_key`（跨应用稳定身份）。
- 已登录用户再次登录：按 `issuer + subject` 匹配复用原账号。
- 明确的**不合并策略**：不会按 username/email 静默合并既有本地账号，
  如需合并由管理员手动处理。

### 1.1 邀请制注册：注册后自动回 magicbook（R217）

登录页的「注册账号 Sign up」按钮**不再**直接指向 Authentik 邀请链接，而是
指向 magicbook 侧的 `/oidc/signup`（同窗口打开，不再 `target="_blank"`）。
该端点把「邀请注册」与「OIDC 授权」串成一条链：

```
/oidc/signup
   │  ① authlib 生成 OIDC 授权 URL（state / nonce / PKCE）→ 存 magicbook session
   │  ② 从 AUTHENTIK_ENROLLMENT_INVITE_URL 解析出 itoken
   │  ③ 把授权 URL 的 path+query 编码成 next，拼成邀请 flow URL
   ▼
https://account.haoshenqi.top/if/flow/invitation-enrollment/?itoken=<pk>&next=...
   │  用户填账号建号（末位 UserLoginStage 建立 Authentik 登录态）
   ▼  flow 完成 → 302 到 next（相对路径的 authorize）
https://account.haoshenqi.top/application/o/authorize/?client_id=..&state=..&nonce=..&redirect_uri=..
   │  已登录 → 签发 code → 302
   ▼
/oidc/callback?code=...&state=...
   ▼
magicbook 首页（**已是登录态**，无需再点一次「Log in」）
```

要点与排障：

- **`next` 必须是相对路径**——Authentik 的 flow 结束逻辑硬性拒绝绝对 URL
  （"Invalid next URL"）。因为 authorize 端点与 flow 同域，本方案把 `next`
  写成同域相对路径 `/application/o/authorize/?...` 正好满足约束。
- **`next` 指向 authorize 而非 magicbook callback**——由 Authentik 负责
  「已登录 → 签发 code → 回调」，magicbook 侧 `callback()` 零改动，
  建号/绑号/角色判定不分叉。
- **itoken 从既有 env 解析**，不新增 `AUTHENTIK_ENROLLMENT_INVITE_TOKEN`；
  轮换邀请只改 `AUTHENTIK_ENROLLMENT_INVITE_URL` 一处。R225 起生成链接只输出
  **顶层** `?itoken=<pk>&next=...`；历史嵌套 `?query=itoken%3D...` 仅为存量 env
  兼容读取，不再生成。
- **注册完成后回 magicbook 的哪个页面**可由 `/oidc/signup?next=...` 指定，
  但只允许站内相对路径（开放重定向防护）。
- **`AUTHENTIK_ENROLLMENT_INVITE_URL` 未配置** → 登录页不渲染注册入口。

详细设计与现网实证见 L3
[`docs/product/admin/features/oidc-self-registration.md`](../../../product/admin/features/oidc-self-registration.md) § 注册后自动回站。

## 2. 配置文件（.env）

OIDC 全部由环境变量配置，`docker-compose.yml` 经 `env_file` 注入，
或 `restart.sh` 直接 `source .env`：

| 环境变量 | 示例 | 说明 |
|---|---|---|
| `AUTHENTIK_ISSUER` | `https://account.haoshenqi.top/application/o/magicbook/` | Authentik Provider 的 issuer（**随请求 Host 变化**，见 §6 域名切换） |
| `AUTHENTIK_MAGICBOOK_CLIENT_ID` | `<client_id>` | Authentik 侧 magicbook application 的 Client ID |
| `AUTHENTIK_MAGICBOOK_CLIENT_SECRET` | `<client_secret>` | 与 id_token 签名/凭证换取相关的密钥 |
| `AUTHENTIK_MAGICBOOK_REDIRECT_URI` | `https://magicbook.haoshenqi.top/oidc/callback` | **回调地址**，授权后 Authentik 重定向到此处；未设置时回退 `url_for(..., _external=True)` |
| `AUTHENTIK_ENROLLMENT_INVITE_URL` | `https://account.haoshenqi.top/if/flow/invitation-enrollment/?itoken=<邀请pk>` | **邀请制注册入口**（R103）。配置后登录页（游客首页）在登录按钮下渲染「注册账号 Sign up (invite)」；**R217 起该按钮改为指向 magicbook 侧 `/oidc/signup`**（由它串起邀请注册与 OIDC 授权，注册完自动回站且已登录），itoken 从本变量的顶层 query 解析，不另设独立变量。⚠️ **R225 现网复核：链接形式必须是顶层 `?itoken=<pk>`**。Authentik 2025.10.2 的 `FlowInterface` 把浏览器原始 `window.location.search` 整体作为 executor API 的 `query` 入参；若再套 `?query=itoken%3D...`，API 收到的是 `query=query%3D...`，会无限 302。2026-10-25 实测顶层形式正常返回注册首步，嵌套形式无限 302。历史嵌套 env 仍兼容读取，但轮换工具只生成顶层形式。**当前策略（2026-10-23 用户拍板）：邀请设为可复用（`single_use=False`）、有效期 90 天**，否则每注册一个人入口就死一次。轮换工具 `scripts/rotate_authentik_invite.py`（建邀请 → 换 .env → `docker compose up -d` 重建 → 校验登录页；`docker restart` 不重读 env_file）。未配置则不渲染注册入口 |

> **当前线上取值（2026-10-23 R161 域名切换后）**
>
> - Issuer：`https://account.haoshenqi.top/application/o/magicbook/`
> - Redirect URI：`https://magicbook.haoshenqi.top/oidc/callback`
> - 注册邀请：`https://account.haoshenqi.top/if/flow/invitation-enrollment/?itoken=…`
> - 旧域 `magicbook.haoyuhang.top` / `authentik.haoshenqi.top` 均保留：前者整站 301 到新域，后者仅浏览器入口 301（OIDC 机器端点原地保留，供 note/immich 等旧 issuer 的 RP 使用）
> - 改这三项须同步 authentik provider 的 `_redirect_uris` 白名单（新旧两条并存）与 moon-well 的 `AUTHENTIK_MAGICBOOK_ISSUER`（换票校验逐字比对 issuer）

## 3. 回调地址（redirect_uri）约束

`cps/oidc.py:67`：

```python
redirect_uri = os.getenv("AUTHENTIK_MAGICBOOK_REDIRECT_URI") or url_for("oidc.callback", _external=True)
```

- 优先使用 `.env` 中的 `AUTHENTIK_MAGICBOOK_REDIRECT_URI`；
- 未配置时按当前请求域名自动生成 `https://<host>/oidc/callback`。
- **必须与 Authentik 侧 application 配置的 Redirect URLs 白名单完全匹配**
  （含协议、域名、路径），否则 Authentik 回调会因
  `redirect_uri mismatch` 被拒绝（`Authorization flow failed`）。

## 4. 常见问题与排障

### 4.1 授权 URL 中的 redirect_uri 是旧域名

- **现象**：`/application/o/authorize/?...&redirect_uri=https%3A%2F%2F<旧域名>%2Foidc%2Fcallback`
- **根因**：`.env` 的 `AUTHENTIK_MAGICBOOK_REDIRECT_URI` 仍为旧域名，而
  `login()` 优先取该值。
- **修复**：改 `.env` 为新域名 → 重启服务（见 §5）→ 同时在 Authentik
  application 的 Redirect URLs 白名单添加新域名回调。

### 4.2 /oidc/callback 返回 500

- **根因（已修复）**：authentik 若以 **HS256 对称签名**生成 id_token，
  jwks_uri 返回空对象 `{}`，authlib 默认 JWKS 校验抛
  `ValueError: Invalid key set format`。`AuthentikOAuth2App.create_load_key`
  已特判：`HS*` 算法用 `client_secret` 做 HMAC 校验，`RS*` 仍走 JWKS
  （并支持强制刷新 JWKS）。
- **排障顺序**：看 `/tmp/calibre-web.log`（或 logs 体积）中 callback 的异常
  堆栈 → 确认签名算法与 jwks_uri 内容 → 确认 `.env` 的 issuer 与
  client_secret 与 Authentik 侧一致。

### 4.3 回调被 Authentik 拒绝 / 无法重定向

- 检查三方域名一致性：登录页域名（`magicbook.haoyuhang.top`）、
  `.env` 的 redirect_uri、Authentik 白名单三处必须统一。
- 检查后仍失败，用浏览器开发者工具抓 authorize 请求，核对
  `client_id / redirect_uri / scope` 是否与 Authentik 配置一致。

### 4.4 本地账号与 OIDC 账号不合并

- 有意行为：`callback()` 仅按 `issuer + subject` 匹配，不会静默合并
  同 username/email 的本地账号（避免错绑）。跨应用身份映射见
  `docs/project/_legacy/feat/sso-user-unification/design/sso-user-unification-design.md`（历史归档）。

### 4.5 注册后没回到 magicbook（停在 Authentik）

- **现象**：点「注册账号」→ 走完邀请注册 → 停在 Authentik 页面，没有自动回 magicbook。
- **可能原因与判别**：
  1. **代码未上线**：R217 的 `/oidc/signup` 端点未部署时，登录页仍渲染旧链接。判据：`curl -sI https://magicbook.haoshenqi.top/oidc/signup` 应返回 **302**（已上线）或 **404**（未上线）。
  2. **flow 报 "Invalid next URL"**：`next` 被写成了绝对 URL。Authentik 硬性要求 `next` 为相对路径（`is_url_absolute` 判 netloc 非空即拒）。
  3. **邀请过期**：现网 invitation `expires` 到期后 Authentik 报 "Invalid invite"——属邀请轮换问题，与本链路无关。
- **判据（看 Authentik 日志）**：`docker logs authentik-server-1` 里搜 `f(exec)` 与 `Invalid next URL`；flow 结束时的 `xak-flow-redirect` 响应的 `to` 字段应是 `/application/o/authorize/?client_id=..` 开头的**相对路径**。

### 4.6 注册后回站了，但提示 state 校验失败

- **根因**：用户注册耗时过长，magicbook 侧 session 中的 `state` 数据已失效或 session 本身过期。
- **修复**：重新点一次「注册账号」走完整流程（不要中途开新标签页）。

## 5. 重启服务使 .env 生效

`.env` 改动后必须重启进程才能加载：

```bash
./restart.sh
```

- 脚本逻辑：按端口找到旧 PID → kill → 重新 `nohup python3 cps.py`（本机默认 8083；UBT 旧部署用 8085）。
- **注意**：`restart.sh` 会 `source .env` 到当前 shell 再启动进程，
  因此无需重建容器；但若走 docker-compose 部署（`env_file`），
  需 `docker compose up -d` 重建容器。
- 验证：

```bash
ps aux | grep "[c]ps.py"            # 确认新 PID
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8083/login   # 期望 200/302（端口按实际部署替换）
```

## 6. 测试

相关测试文件：

- `tests/test_oidc.py`：OIDC 配置加载、HS256 id_token 签名校验、
  未配置环境变量时的行为。
- `tests/test_oidc_signup.py`（R217）：`/oidc/signup` 的 302 目标、
  `next` 为相对路径且指向 `/application/o/authorize/`、`state` 与 session 一致、
  开放重定向防护、登录页按钮指向与不再 `target=_blank`。
- `tests/test_oidc_admin_role.py`（R211）：新账号角色判定与降级 CLI。

> 注：早期版本文档提到的 `tests/test_user_key.py` **当前仓库不存在**，
> 相关断言已并入上述文件。

运行：

```bash
pytest tests/test_oidc.py tests/test_oidc_signup.py tests/test_oidc_admin_role.py -q
```
