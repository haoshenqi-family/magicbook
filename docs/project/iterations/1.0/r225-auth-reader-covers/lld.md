# R225 注册跳转 / 普通账号阅读权限 / 品牌封面占位（LLD）

状态：已上线待验收（2026-10-25）

## 1. 缺陷与目标

| # | 现象 | 根因 | 目标 |
| --- | --- | --- | --- |
| 1 | `/login` 点注册后在 Authentik 报 `Invalid invite/invite not found` | `/oidc/signup` 把 `itoken` / `next` 二次编码到 `?query=`，Authentik 2025.10.2 的 executor 又整体接收浏览器 search，最终 API 收到 `query=query%3D...`，无法解析邀请 | `/oidc/signup` 与轮换脚本只生成顶层 `?itoken=...&next=...` |
| 2 | 所有普通账号 `/read/<id>/<format>`、`/download` 403 | 生产 `config_default_role=0`；OIDC 新账号严格继承该值，不含 `ROLE_VIEWER(256)` 或 `ROLE_DOWNLOAD(2)` | 新账号固定补 `ROLE_VIEWER`；存量账号由点名 CLI 修正；详情页分别说明 View 与 Download 权限如何开通 |
| 3 | 首页多个无封面书显示白底黑字 `Cover not available` | `generic_cover.jpg` 是旧上游占位图 | 换成与站内圆章一致的深墨绿品牌封面，所有缺封面路径继续共用同一张 |

## 2. 取舍

- **阅读与下载分开**：本次只把 `ROLE_VIEWER` 设为新账号基础能力。`ROLE_DOWNLOAD` 保持独立，避免“修阅读”顺手开放整本文件下载。
- **管理员仍只由人工赋予**：`site_default_role()` 继续剔除 `ROLE_ADMIN`，R211 安全边界不变。
- **存量不自动改**：生产库存在老账号，但自动批量提权不可审计。`scripts/reader_role_audit.py` 默认 dry-run，必须点名 `--ids` / `--emails`，写前备份。`scripts/oidc_admin_audit.py --demote` 的目标角色同步改为「默认角色 + `ROLE_VIEWER` - `ROLE_ADMIN`」，避免修完管理员位又留下阅读 403。
- **邀请兼容读取**：`_invite_token()` 仍识别历史 `?query=itoken%3D...` env，避免部署瞬间关闭注册；生成侧只输出顶层参数。

## 3. 实现点

### 3.1 注册跳转

`cps/oidc.py`：

```text
flow_query = urlencode({"itoken": invite_token, "next": target})
signup_url = flow_path + "?" + flow_query
```

`scripts/rotate_authentik_invite.py`：

```text
build_invite_url(...) -> .../?itoken=<pk>
```

### 3.2 阅读权限

```text
site_default_role():
  role = config_default_role or 0
  role |= ROLE_VIEWER
  role &= ~ROLE_ADMIN
```

详情页在 `entry.reader_list` 存在但当前账号无 `role_viewer()` 时显示：

-「Reading access is not enabled for this account」
-「Ask an administrator to enable “View” in Users → Edit User for your account.」

详情页在 `entry.data` 存在但当前账号无 `role_download()` 时另行显示：

-「Download access is not enabled for this account」
-「Ask an administrator to enable “Download” in Users → Edit User for your account.」

### 3.3 封面

- 文件：`cps/static/generic_cover.jpg`，564×800 JPEG。
- 视觉：站内品牌圆章 + 深墨绿纸纹 + 暖金规则线 + `MAGICBOOK` 字标。
- 接线：沿用 `get_cover_on_failure()`，不改图片 URL 与缓存语义。

## 4. 验证

| 范围 | 命令 / 证据 |
| --- | --- |
| 注册跳转 | `tests/test_oidc_signup.py`：顶层参数、相对 next、state 一致、历史 env 兼容 |
| 阅读权限 | `tests/test_oidc_admin_role.py` + `tests/test_reader_role_audit_r225.py`：新账号与降级目标均有 viewer、无自动 download/admin；两个 CLI 都默认 dry-run、点名、备份、位保持 |
| 详情提示 | `tests/test_auth_reader_covers_r225.py`：View / Download 两条无权限说明与中文 MO 均已守卫 |
| 封面 | 同文件：JPEG 564×800、四角与中心均为品牌深墨绿；`helper.py` 单点回落 |
| 总回归 | 定向 **90 passed / 0 failed**；全量 **961 passed / 0 failed**（4 个非阻断 warning）；`git diff --check` 与改动 Python 文件编译通过 |
| 生产部署 | `890bc6072de413d78ecfb8c9c62f1fba66c5f4ba` 已由 fnOS 手动补跑同一构建脚本上线；容器 `healthy`，镜像 label `house.build-sha` 与提交一致，代码指纹 `f4556c5b4ea0df84` |
| 生产核验 | `/oidc/signup?next=/read/223/epub` 为 302，顶层只有 `itoken` / `next`，无 `query`；关注后 Authentik 返回 200 邀请页。`/static/generic_cover.jpg` 为 81,048 字节，564×800，与仓库 blob 的 SHA-256 一致 |

## 5. 边界

- Authentik 邀请本身过期仍会报 invite 错，属运维轮换，不由本修复掩盖。
- 存量账号修正脚本只改 `user.role`，不动 OIDC subject、会话与书库权限。
- 新账号有阅读权限不等于有下载权限；`/download` 仍由 `ROLE_DOWNLOAD` 独立门禁。
- 品牌封面是统一兜底，不代表书目真实封面；详情页仍尝试读取 `cover.jpg`。
- 生产存量账号 `uxprobe2`（id=9）与 `uxprobe`（id=10）仍为 `role=0`，不会因代码上线自动获得阅读权限；需另行批准后点名执行修正脚本。
