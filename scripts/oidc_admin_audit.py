#!/usr/bin/env python3
"""R211 存量 OIDC 管理员排查 / 降级 CLI（默认 dry-run，stdlib only）。

背景：2026-10-23 之前 `cps/oidc.py` 建号写死 `constants.ADMIN_USER_ROLES`，
任何自助注册（公开邀请链接）的账号都是超管。代码修复只影响新账号，存量必须
单独排查并按需降级，故有此脚本。

用法：
    # 只读：列出所有仍带管理员位的 OIDC 账号（不写库）
    python3 scripts/oidc_admin_audit.py
    # 同上 + 导出 JSON 清单（供人工复核）
    python3 scripts/oidc_admin_audit.py --json /tmp/r211-admins.json
    # 按 id / 邮箱点名降级（写库前自动备份 app.db）
    python3 scripts/oidc_admin_audit.py --demote --ids 4,7
    python3 scripts/oidc_admin_audit.py --demote --emails a@b.com,c@d.com

安全边界（有意为之）：
- 默认 dry-run，绝不写库；`--demote` 必须显式给 `--ids` 或 `--emails`，**不支持全量降级**
  —— 管理员位一旦被批量抹掉只能靠备份回滚。
- 写库前把库文件复制为 `<db>.r211-bak-<时间戳>`，并回显备份路径。
- `OIDC_ADMIN_EMAILS` 白名单内的账号即使被点名也跳过（避免把站长本人降权）。
- 站点默认角色若含管理员位，拒绝执行降级（目标角色本身就不安全）。

不依赖 Flask 应用：只读 SQLite 的 `user` / `settings` 两张表，常量与
`cps/constants.py` 同源（`tests/test_oidc_admin_audit.py` 有对账守卫）。
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
import time

# 与 cps/constants.py:62 的 ROLE_ADMIN 同源；本脚本刻意不 import cps（导入包会
# 触发整个 Flask 应用初始化），改由测试断言两者一致。
ROLE_ADMIN = 1 << 0


def _resolve_db_path(explicit=None):
    """定位 app.db：显式参数 > CONFIG_PATH > 仓库根。"""
    if explicit:
        return os.path.abspath(explicit)
    config_path = os.getenv("CONFIG_PATH", "").strip()
    if config_path:
        candidate = os.path.join(config_path, "app.db")
        if os.path.exists(candidate):
            return os.path.abspath(candidate)
    return os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.db"))


def has_flag(value, bit_flag):
    """与 cps/constants.has_flag 同义：value 是否置了 bit_flag 位。"""
    return bit_flag == (bit_flag & (value or 0))


def connect_readonly(db_path):
    if not os.path.exists(db_path):
        raise SystemExit(f"找不到数据库：{db_path}")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def load_rows(conn):
    """读取全量账号，标注管理员位 / 是否经 OIDC 登录过。"""
    cur = conn.execute("SELECT id, name, email, role, oidc_subject FROM user ORDER BY id")
    rows = []
    for uid, name, email, role, oidc_subject in cur.fetchall():
        role_value = role or 0
        rows.append({
            "id": uid,
            "name": name or "",
            "email": (email or "").strip(),
            "role": role_value,
            "is_admin": has_flag(role_value, ROLE_ADMIN),
            "via_oidc": bool((oidc_subject or "").strip()),
            "oidc_subject": (oidc_subject or "").strip(),
        })
    return rows


def load_default_role(conn):
    """站点「新用户默认角色」；读不到时按最小权限 0。"""
    try:
        row = conn.execute("SELECT config_default_role FROM settings LIMIT 1").fetchone()
    except sqlite3.Error:
        return 0
    if not row or row[0] is None:
        return 0
    return int(row[0])


def admin_emails_from_env(raw=None):
    if raw is None:
        raw = os.getenv("OIDC_ADMIN_EMAILS", "")
    return {item.strip().lower() for item in (raw or "").split(",") if item.strip()}


def plan_demotions(rows, ids=None, emails=None, default_role=0, admin_emails=None):
    """计算降级计划，返回 (targets, skipped)。

    skipped 里带原因，便于在真机上判断是「已无需处理」还是「被保护」。
    目标必须显式点名（ids / emails 至少一个），否则抛 ValueError——批量
    降级不做默认行为。
    """
    ids = {int(i) for i in (ids or [])}
    emails = {e.strip().lower() for e in (emails or []) if e.strip()}
    admin_emails = admin_emails or set()
    if not ids and not emails:
        raise ValueError("降级必须显式指定 --ids 或 --emails（不支持全量降级）")
    if has_flag(default_role, ROLE_ADMIN):
        raise ValueError(
            f"站点默认角色（{default_role}）含管理员位，降级目标不安全；"
            "请先在管理后台调整「新用户默认角色」")

    targets, skipped = [], []
    for row in rows:
        named = row["id"] in ids or (row["email"] and row["email"].lower() in emails)
        if not named:
            continue
        if not row["is_admin"]:
            skipped.append((row, "本就不含管理员位"))
        elif row["email"] and row["email"].lower() in admin_emails:
            skipped.append((row, "命中 OIDC_ADMIN_EMAILS 白名单，跳过"))
        elif row["role"] == default_role:
            skipped.append((row, "角色已等于默认角色"))
        else:
            targets.append(row)
    return targets, skipped


def backup_db(db_path):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = f"{db_path}.r211-bak-{stamp}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def apply_demotions(db_path, targets, default_role):
    """把 targets 的 role 改写为默认角色；返回受影响行数。"""
    if not targets:
        return 0
    conn = sqlite3.connect(db_path)
    try:
        conn.executemany("UPDATE user SET role = ? WHERE id = ?",
                         [(default_role, row["id"]) for row in targets])
        conn.commit()
        return len(targets)
    finally:
        conn.close()


def render_table(rows):
    if not rows:
        return "（无）"
    header = f"{'id':>4}  {'账号':<16} {'邮箱':<30} {'角色':>5}  {'OIDC':<5}"
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(f"{row['id']:>4}  {row['name'][:16]:<16} {row['email'][:30]:<30} "
                     f"{row['role']:>5}  {'是' if row['via_oidc'] else '否':<5}")
    return "\n".join(lines)


def build_parser():
    parser = argparse.ArgumentParser(
        description="R211 存量 OIDC 管理员排查 / 降级（默认 dry-run）")
    parser.add_argument("--db", help="app.db 路径（默认 CONFIG_PATH/app.db 或仓库根 app.db）")
    parser.add_argument("--json", metavar="FILE", help="把管理员清单导出为 JSON")
    parser.add_argument("--demote", action="store_true", help="执行降级（需配 --ids/--emails）")
    parser.add_argument("--ids", help="要降级的账号 id，逗号分隔")
    parser.add_argument("--emails", help="要降级的账号邮箱，逗号分隔")
    parser.add_argument("--all-oidc", action="store_true",
                        help="只读模式：连非管理员也列出（排查用）")
    return parser


def _split(raw):
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def main(argv=None):
    args = build_parser().parse_args(argv)
    db_path = _resolve_db_path(args.db)
    conn = connect_readonly(db_path)
    try:
        rows = load_rows(conn)
        default_role = load_default_role(conn)
    finally:
        conn.close()

    admin_emails = admin_emails_from_env()
    shown = [r for r in rows if args.all_oidc or r["is_admin"]]
    oidc_admins = [r for r in rows if r["is_admin"] and r["via_oidc"]]

    print(f"数据库：{db_path}")
    print(f"站点默认角色：{default_role}"
          f"（{'含管理员位 ⚠️' if has_flag(default_role, ROLE_ADMIN) else '不含管理员位'}）")
    print(f"管理员白名单：{', '.join(sorted(admin_emails)) or '（空）'}")
    print(f"账号总数 {len(rows)}｜管理员 {sum(1 for r in rows if r['is_admin'])}"
          f"｜其中经 OIDC 登录过 {len(oidc_admins)}")
    print()
    print(render_table(shown))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"db": db_path, "default_role": default_role,
                       "admin_emails": sorted(admin_emails),
                       "admins": shown}, fh, ensure_ascii=False, indent=2)
        print(f"\n清单已导出：{args.json}")

    if not args.demote:
        print("\n[dry-run] 未写库。确认清单后用 --demote --ids/--emails 降级。")
        return 0

    try:
        targets, skipped = plan_demotions(
            rows, ids=_split(args.ids), emails=_split(args.emails),
            default_role=default_role, admin_emails=admin_emails)
    except ValueError as exc:
        print(f"\n拒绝执行：{exc}")
        return 2

    for row, reason in skipped:
        print(f"跳过 id={row['id']} {row['email'] or row['name']}：{reason}")
    if not targets:
        print("\n没有可降级的账号，未写库。")
        return 0

    print(f"\n将把 {len(targets)} 个账号降级为角色 {default_role}：")
    print(render_table(targets))
    backup_path = backup_db(db_path)
    print(f"已备份：{backup_path}")
    changed = apply_demotions(db_path, targets, default_role)
    print(f"已改写 {changed} 行。回滚方式：停容器后用备份覆盖 {db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
