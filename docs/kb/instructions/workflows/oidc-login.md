# Overview：Authentik OIDC 登录说明

> 功能路径：`/oidc/login` → Authentik 授权 → `/oidc/callback`
> 相关代码：`cps/oidc.py`
> 适用版本：magicbook（Calibre-Web fork，Python/Flask + Gevent，默认端口 8085）

## 1. 功能概述

magicbook 以 **Authentik** 作为统一身份源（IdP），用户可从登录页经
OIDC（OpenID Connect）授权码模式登录：

```
用户访问 /oidc/login                         （登录页「Authentik 登录」按钮）
   │  302 跳转到 Authentik 授权页
   ▼
https://authentik.haoshenqi.top/application/o/authorize/?
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

## 2. 配置文件（.env）

OIDC 全部由环境变量配置，`docker-compose.yml` 经 `env_file` 注入，
或 `restart.sh` 直接 `source .env`：

| 环境变量 | 示例 | 说明 |
|---|---|---|
| `AUTHENTIK_ISSUER` | `https://authentik.haoshenqi.top/application/o/magicbook/` | Authentik Provider 的 issuer |
| `AUTHENTIK_MAGICBOOK_CLIENT_ID` | `<client_id>` | Authentik 侧 magicbook application 的 Client ID |
| `AUTHENTIK_MAGICBOOK_CLIENT_SECRET` | `<client_secret>` | 与 id_token 签名/凭证换取相关的密钥 |
| `AUTHENTIK_MAGICBOOK_REDIRECT_URI` | `https://magicbook.haoyuhang.top/oidc/callback` | **回调地址**，授权后 Authentik 重定向到此处；未设置时回退 `url_for(..., _external=True)` |

> **当前线上取值（2026-08-21 修订后）**
>
> - Issuer 不变：`https://authentik.haoshenqi.top/application/o/magicbook/`
> - Redirect URI：`https://magicbook.haoyuhang.top/oidc/callback`

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
  `docs/feat/sso-user-unification/design/sso-user-unification-design.md`。

## 5. 重启服务使 .env 生效

`.env` 改动后必须重启进程才能加载：

```bash
./restart.sh
```

- 脚本逻辑：根据 8085 端口找到旧 PID → kill → 重新 `nohup python3 cps.py`。
- **注意**：`restart.sh` 会 `source .env` 到当前 shell 再启动进程，
  因此无需重建容器；但若走 docker-compose 部署（`env_file`），
  需 `docker compose up -d` 重建容器。
- 验证：

```bash
ps aux | grep "[c]ps.py"            # 确认新 PID
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8085/login   # 期望 200/302
```

## 6. 测试

相关测试文件：

- `tests/test_oidc.py`：OIDC 配置加载、HS256 id_token 签名校验、
  未配置环境变量时的行为。
- `tests/test_user_key.py`：OIDC 首次登录创建的用户 `user_key == sub`、
  回填幂等、callback 预绑定匹配。

运行：

```bash
pytest tests/test_oidc.py tests/test_user_key.py -q
```