#!/usr/bin/env python3
"""轮换 magicbook 的 Authentik 邀请制注册链接（R211 配套运维工具 · stdlib only）。

为什么需要这个脚本
------------------
登录页「注册账号 Sign up (invite)」指向 `.env` 的 `AUTHENTIK_ENROLLMENT_INVITE_URL`
——一条具体的 Authentik 邀请。**链接形式一变，这条入口就整体报废，而且失效只
表现为「点进去报 Invalid invite」或无限跳转，不会有人来报「注册不了」**。
2026-10-25 R225 现网复核：Authentik 2025.10.2 接受顶层 `?itoken=<uuid>`
及其 `next`；再包一层 `?query=itoken%3D<uuid>` 反而会让 executor API
无限 302。邀请记录本身一直好着——`single_use=false`、未过期。

本脚本把「建邀请 → 换 .env → 重启容器 → 校验」串成一条命令，避免下次再靠人肉。

用法
----
```bash
# 1) 取 token（fnOS 上；AUTHENTIK_TOKEN 即 authentik 的 bootstrap/superuser token）
#    ssh root@192.168.31.9 "grep -E 'AUTHENTIK_TOKEN:' /app/authentik/docker-compose.yml | head -1"

# 2) 干跑：只创建邀请并打印新链接，不碰任何服务器
export AUTHENTIK_TOKEN=...
python3 scripts/rotate_authentik_invite.py --name magicbook-r211

# 3) 一条命令全流程：创建邀请 → 改 fnOS .env → 重建容器 → 校验登录页
python3 scripts/rotate_authentik_invite.py --name magicbook-r211 --apply \
    --ssh-host 192.168.31.9 --magicbook-dir /vol1/1000/app/magicbook
```

关键细节
--------
- **默认 `single_use=False`（可复用）**：2026-10-23 用户拍板「登录页那条注册链接
  要长期有效」——一次性邀请用过就废，入口会周期性坏死（R103 那条就是这么报废的）。
  风险由 R211 兜底：转发出去也只产生普通用户，管理员仍由人工赋予。
  需要一次性时加 `--single-use`。
- **链接形式**：脚本生成的是 `?itoken=<uuid>`（R225 现网复核后的正确形式，
  见 `build_invite_url` 的注释）。
- **必须 `docker compose up -d` 重建，不能 `docker restart`**：`env_file` 只在容器
  创建时注入进程环境，`restart` 不会重读 `.env`；而 `cps/web.py` 每次请求读
  `os.getenv("AUTHENTIK_ENROLLMENT_INVITE_URL")`，所以新链接必须进到进程环境。
- 默认 dry-run：没有 `--apply` 时只创建邀请并打印，不改任何服务器文件。
- token 只从环境变量 / 文件读，**不落日志、不落盘、不进对话**。
- `.env` 改动前自动备份为 `.env.bak-invite-<时间戳>`。
"""
import argparse
import datetime
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_AUTHENTIK_URL = "https://account.haoshenqi.top"
DEFAULT_MAGICBOOK_URL = "https://magicbook.haoshenqi.top"
INVITE_FLOW = "invitation-enrollment"


def _http_json(url, method="GET", body=None, headers=None, timeout=20):
    data = None
    hdrs = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw.strip().startswith(("{", "[")) else raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        return exc.code, raw
    except Exception as exc:  # noqa: BLE001 - 网络错误要给出可读信息
        return 0, str(exc)


def create_invitation(base_url, token, name, expires_at=None, flow=INVITE_FLOW,
                      single_use=True):
    """创建一条 Authentik 邀请，返回 (pk, 新建对象)。

    端点与请求体规格取自实例自己的 OpenAPI（`/api/v3/schema/?format=json`），
    **不是**凭记忆写的 `/api/v3/core/invitations/`——那个路径在本实例上不存在
    （404/405）。真实端点：`POST /api/v3/stages/invitation/invitations/`，
    body `InvitationRequest`：`name`（必填）、`expires`、`flow`、`fixed_data`、
    `single_use`；响应含 `pk`（即邀请的 itoken）。
    """
    endpoint = base_url.rstrip("/") + "/api/v3/stages/invitation/invitations/"
    headers = {"Authorization": "Bearer " + token}
    payload = {"name": name, "flow": flow, "single_use": single_use}
    if expires_at:
        payload["expires"] = expires_at
    status, resp = _http_json(endpoint, method="POST", body=payload, headers=headers)
    if status in (200, 201) and isinstance(resp, dict) and resp.get("pk"):
        return resp["pk"], resp
    raise SystemExit(f"创建邀请失败（HTTP {status}）：{str(resp)[:400]}")


def build_invite_url(base_url, pk):
    """拼出可用的邀请链接。

    ⚠️ **形式必须是顶层参数**：2026-10-25 对现网 Authentik 2025.10.2 实测，
    `FlowInterface-2025.10.2.js` 把浏览器完整 `window.location.search` 作为
    `flowsExecutorGet(query=...)` 的入参；`?itoken=<uuid>` 能返回注册首步，
    而 `?query=itoken%3D<uuid>` 会让 API 收到 `query=query%3D...` 并无限 302。
    因此这里只生成顶层 itoken，不再预编码一层 query。
    """
    query = urllib.parse.urlencode({"itoken": pk})
    return f"{base_url.rstrip('/')}/if/flow/{INVITE_FLOW}/?{query}"


def _ssh(host, command, timeout=120):
    proc = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", f"root@{host}", command],
        capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise SystemExit(f"ssh {host} 失败：{proc.stderr.strip()[:300]}")
    return proc.stdout


def apply_to_magicbook(ssh_host, magicbook_dir, invite_url, service="magicbook"):
    """改 fnOS 上的 .env 并重建容器，让新链接进到进程环境。"""
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    env_path = f"{magicbook_dir}/.env"
    quoted = shlex.quote(invite_url)
    cmd = (
        f"set -e; cd {shlex.quote(magicbook_dir)}; "
        f"cp .env .env.bak-invite-{stamp}; "
        f"if grep -q '^AUTHENTIK_ENROLLMENT_INVITE_URL=' .env; then "
        f"sed -i 's|^AUTHENTIK_ENROLLMENT_INVITE_URL=.*|AUTHENTIK_ENROLLMENT_INVITE_URL={quoted}|' .env; "
        f"else printf '\\nAUTHENTIK_ENROLLMENT_INVITE_URL={quoted}\\n' >> .env; fi; "
        f"grep -E '^AUTHENTIK_ENROLLMENT_INVITE_URL=' .env; "
        f"docker compose up -d {service}"
    )
    print(f"→ 更新 {ssh_host}:{env_path} 并重建容器（备份 .env.bak-invite-{stamp}）")
    return _ssh(ssh_host, cmd, timeout=300)


def verify_login_page(magicbook_url, expect_itoken):
    """校验登录页渲染的邀请链接已换成新 token。"""
    status, html = _http_json(magicbook_url.rstrip("/") + "/login", timeout=25)
    if isinstance(html, str) and "itoken=" in html:
        found = re.search(r"itoken=([0-9a-zA-Z\-]+)", html)
        got = found.group(1) if found else ""
        ok = got == expect_itoken
        print(f"→ 登录页邀请 token：{got}（期望 {expect_itoken}）{'✅ 一致' if ok else '❌ 不一致'}")
        return ok
    print(f"→ 登录页未渲染邀请链接（HTTP {status}）——检查 .env 是否已注入并重建容器")
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="轮换 magicbook 的 Authentik 邀请制注册链接（默认 dry-run）")
    parser.add_argument("--authentik-url", default=DEFAULT_AUTHENTIK_URL)
    parser.add_argument("--magicbook-url", default=DEFAULT_MAGICBOOK_URL)
    parser.add_argument("--name", default="magicbook-invite", help="邀请备注名")
    parser.add_argument("--expires-days", type=int, default=90,
                        help="邀请有效期天数（authentik 默认 30 天；可复用模式下给 90 天）")
    parser.add_argument("--single-use", action="store_true",
                        help="把邀请设为一次性（single_use=True）。默认是**可复用**——"
                             "2026-10-23 用户拍板：登录页那条注册链接要长期有效，"
                             "否则每注册一个人入口就死一次")
    parser.add_argument("--token-file", help="从文件读 AUTHENTIK_TOKEN（默认读环境变量）")
    parser.add_argument("--apply", action="store_true",
                        help="真正改 fnOS 上的 .env 并重建容器（默认只建邀请并打印）")
    parser.add_argument("--ssh-host", default="192.168.31.9")
    parser.add_argument("--magicbook-dir", default="/vol1/1000/app/magicbook")
    parser.add_argument("--service", default="magicbook")
    args = parser.parse_args(argv)

    token = ""
    if args.token_file:
        with open(args.token_file, "r", encoding="utf-8") as fh:
            token = fh.read().strip()
    else:
        token = os.getenv("AUTHENTIK_TOKEN", "").strip()
    if not token:
        raise SystemExit("缺少 AUTHENTIK_TOKEN：设环境变量或用 --token-file 指向文件")

    expires_at = None
    if args.expires_days > 0:
        expires_at = (datetime.datetime.now(datetime.timezone.utc)
                      + datetime.timedelta(days=args.expires_days)
                      ).strftime("%Y-%m-%dT%H:%M:%SZ")

    pk, obj = create_invitation(args.authentik_url, token, args.name, expires_at,
                                single_use=args.single_use)
    url = build_invite_url(args.authentik_url, pk)
    print(f"✅ 新邀请已创建：pk={pk}")
    print(f"   链接：{url}")
    print(f"   有效期：{expires_at or '（不限）'}")

    if not args.apply:
        print("\n[dry-run] 未改任何服务器配置。把上面的链接写入 fnOS 的 .env 并"
              " `docker compose up -d magicbook` 后才会生效。")
        return 0

    apply_to_magicbook(args.ssh_host, args.magicbook_dir, url, args.service)
    ok = verify_login_page(args.magicbook_url, pk)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
