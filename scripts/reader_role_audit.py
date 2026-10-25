#!/usr/bin/env python3
"""R225 存量读者权限修正 CLI（默认 dry-run，stdlib only）。

背景：R225 之前 OIDC 新账号严格继承站点默认角色；生产库
`config_default_role=0` 时，新账号连在线阅读（ROLE_VIEWER=256）都没有，
表现为书能看、详情能进、点“继续阅读”一律 403。

代码修复只影响新账号。存量账号必须点名修正，故本脚本：
- 默认只读，列出缺少阅读位的 OIDC 账号；
- `--grant-viewer` 必须显式给 `--ids` 或 `--emails`，不支持全量；
- 只补 ROLE_VIEWER，不碰 ROLE_DOWNLOAD / ROLE_ADMIN 和其他角色位；
- 写库前备份 app.db。

用法：
    python3 scripts/reader_role_audit.py
    python3 scripts/reader_role_audit.py --json /tmp/readers.json
    python3 scripts/reader_role_audit.py --grant-viewer --ids 9,10
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
import time


# 与 cps/constants.py 同源；脚本刻意不 import cps（导入会拉起 Flask 应用）。
ROLE_VIEWER = 1 << 8


def _resolve_db_path(explicit=None):
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
    return bit_flag == (bit_flag & (value or 0))


def load_rows(conn):
    cur = conn.execute(
        "SELECT id, name, email, role, oidc_subject FROM user ORDER BY id")
    rows = []
    for uid, name, email, role, oidc_subject in cur.fetchall():
        role_value = role or 0
        rows.append({
            "id": uid,
            "name": name or "",
            "email": (email or "").strip(),
            "role": role_value,
            "can_read": has_flag(role_value, ROLE_VIEWER),
            "is_admin": has_flag(role_value, 1),
            "via_oidc": bool((oidc_subject or "").strip()),
        })
    return rows


def plan_grants(rows, ids=None, emails=None):
    """返回 (targets, skipped)；必须点名，且只处理缺少阅读位的账号。"""
    ids = {int(i) for i in (ids or [])}
    emails = {e.strip().lower() for e in (emails or []) if e.strip()}
    if not ids and not emails:
        raise ValueError("修正必须显式指定 --ids 或 --emails（不支持全量）")

    targets, skipped = [], []
    for row in rows:
        named = row["id"] in ids or (
            row["email"] and row["email"].lower() in emails)
        if not named:
            continue
        if row["can_read"]:
            skipped.append((row, "已具备阅读权限"))
        else:
            targets.append(row)
    return targets, skipped


def apply_grants(db_path, targets):
    if not targets:
        return 0
    conn = sqlite3.connect(db_path)
    try:
        conn.executemany(
            "UPDATE user SET role = COALESCE(role, 0) | ? WHERE id = ?",
            [(ROLE_VIEWER, row["id"]) for row in targets])
        conn.commit()
        return len(targets)
    finally:
        conn.close()


def backup_db(db_path):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = f"{db_path}.r225-bak-{stamp}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def render_table(rows):
    if not rows:
        return "（无）"
    header = f"{'id':>4}  {'账号':<16} {'邮箱':<30} {'角色':>5}  {'可阅读':<6}"
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(
            f"{row['id']:>4}  {row['name'][:16]:<16} "
            f"{row['email'][:30]:<30} {row['role']:>5}  "
            f"{'是' if row['can_read'] else '否':<6}")
    return "\n".join(lines)


def build_parser():
    parser = argparse.ArgumentParser(
        description="R225 存量账号阅读权限排查 / 修正（默认 dry-run）")
    parser.add_argument("--db", help="app.db 路径（默认 CONFIG_PATH/app.db 或仓库根 app.db）")
    parser.add_argument("--json", metavar="FILE", help="把缺阅读权限的账号清单导出为 JSON")
    parser.add_argument("--grant-viewer", action="store_true",
                        help="补 ROLE_VIEWER（需配 --ids/--emails）")
    parser.add_argument("--ids", help="账号 id，逗号分隔")
    parser.add_argument("--emails", help="账号邮箱，逗号分隔")
    return parser


def _split(raw):
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def main(argv=None):
    args = build_parser().parse_args(argv)
    db_path = _resolve_db_path(args.db)
    if not os.path.exists(db_path):
        raise SystemExit(f"找不到数据库：{db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = load_rows(conn)
    finally:
        conn.close()

    missing = [row for row in rows if not row["can_read"]]
    print(f"数据库：{db_path}")
    print(f"账号总数 {len(rows)}｜缺少阅读权限 {len(missing)}")
    print()
    print(render_table(missing))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"db": db_path, "missing_viewer": missing},
                      fh, ensure_ascii=False, indent=2)
        print(f"\n清单已导出：{args.json}")

    if not args.grant_viewer:
        print("\n[dry-run] 未写库。确认清单后用 "
              "--grant-viewer --ids/--emails 修正。")
        return 0

    try:
        targets, skipped = plan_grants(
            rows, ids=_split(args.ids), emails=_split(args.emails))
    except ValueError as exc:
        print(f"\n拒绝执行：{exc}")
        return 2

    for row, reason in skipped:
        print(f"跳过 id={row['id']} {row['email'] or row['name']}：{reason}")
    if not targets:
        print("\n没有需要修正的账号，未写库。")
        return 0

    print(f"\n将给 {len(targets)} 个账号补 ROLE_VIEWER（不影响下载/管理员权限）：")
    print(render_table(targets))
    backup_path = backup_db(db_path)
    print(f"已备份：{backup_path}")
    changed = apply_grants(db_path, targets)
    print(f"已改写 {changed} 行。回滚方式：停容器后用备份覆盖 {db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
