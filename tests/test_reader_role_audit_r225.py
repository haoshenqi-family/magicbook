"""R225 存量读者权限 CLI：只读默认、点名修正、只补阅读位。"""
import importlib.util
import os
import sqlite3
import sys

import pytest

from cps import constants


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPT = os.path.join(ROOT, "scripts", "reader_role_audit.py")
_spec = importlib.util.spec_from_file_location("reader_role_audit_r225", _SCRIPT)
audit = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("reader_role_audit_r225", audit)
_spec.loader.exec_module(audit)


def _make_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE user (id INTEGER PRIMARY KEY, name VARCHAR(64), "
                 "email VARCHAR(64), role SMALLINT, oidc_subject VARCHAR(255))")
    conn.executemany(
        "INSERT INTO user (id, name, email, role, oidc_subject) VALUES (?,?,?,?,?)",
        [(1, "admin", "admin@example.org", constants.ADMIN_USER_ROLES, None),
         (9, "uxprobe2", "probe2@example.com", 0, "sub-9"),
         (10, "uxprobe", "probe@example.com", constants.ROLE_DOWNLOAD, "sub-10"),
         (11, "reader", "reader@example.com", constants.ROLE_VIEWER, "sub-11")])
    conn.commit()
    conn.close()


def test_constants_match_cps():
    assert audit.ROLE_VIEWER == constants.ROLE_VIEWER


def test_default_role_grants_viewer_but_not_download():
    from cps import oidc

    role = oidc.resolve_new_user_role()
    assert constants.has_flag(role, constants.ROLE_VIEWER)
    assert not constants.has_flag(role, constants.ROLE_DOWNLOAD)
    assert not constants.has_flag(role, constants.ROLE_ADMIN)


def test_dry_run_lists_missing_and_does_not_write(tmp_path, capsys):
    db = str(tmp_path / "app.db")
    _make_db(db)
    assert audit.main(["--db", db]) == 0
    out = capsys.readouterr().out
    assert "缺少阅读权限 2" in out
    assert "uxprobe2" in out and "uxprobe" in out
    assert "已改写" not in out
    conn = sqlite3.connect(db)
    try:
        roles = dict(conn.execute("SELECT id, role FROM user"))
    finally:
        conn.close()
    assert roles[9] == 0 and roles[10] == constants.ROLE_DOWNLOAD


def test_grant_requires_explicit_targets(tmp_path, capsys):
    db = str(tmp_path / "app.db")
    _make_db(db)
    assert audit.main(["--db", db, "--grant-viewer"]) == 2
    assert "不支持全量" in capsys.readouterr().out


def test_grant_only_adds_viewer_and_keeps_other_bits(tmp_path, capsys):
    db = str(tmp_path / "app.db")
    _make_db(db)
    assert audit.main(["--db", db, "--grant-viewer", "--ids", "9,10"]) == 0
    conn = sqlite3.connect(db)
    try:
        roles = dict(conn.execute("SELECT id, role FROM user"))
    finally:
        conn.close()
    assert roles[9] == constants.ROLE_VIEWER
    assert roles[10] == (constants.ROLE_DOWNLOAD | constants.ROLE_VIEWER)
    assert roles[1] == constants.ADMIN_USER_ROLES
    assert any(".r225-bak-" in name for name in os.listdir(str(tmp_path)))
    assert "已改写 2 行" in capsys.readouterr().out


def test_already_readable_account_is_skipped(tmp_path, capsys):
    db = str(tmp_path / "app.db")
    _make_db(db)
    assert audit.main(["--db", db, "--grant-viewer", "--ids", "11"]) == 0
    out = capsys.readouterr().out
    assert "已具备阅读权限" in out
    assert "没有需要修正的账号" in out
