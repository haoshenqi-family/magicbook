"""R211 守卫：OIDC 自助注册不再默认授予管理员权限。

三个层面各钉一条：
1. 决策函数 `resolve_new_user_role`——白名单命中才给管理员，否则站点默认角色；
2. 回调建号形制——`cps/oidc.py` 建号处不得再出现 `ADMIN_USER_ROLES` 直写；
3. 存量排查 CLI——清单可导出、降级必须点名、白名单受保护、写库前留备份。
"""
import importlib.util
import inspect
import os
import sqlite3
import sys

import pytest

from cps import constants, oidc

_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "scripts", "oidc_admin_audit.py")
_spec = importlib.util.spec_from_file_location("oidc_admin_audit", _SCRIPT)
audit = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("oidc_admin_audit", audit)
_spec.loader.exec_module(audit)


class TestResolveNewUserRole:
    def test_普通邮箱拿到站点默认角色(self):
        assert oidc.resolve_new_user_role(
            "reader@example.com", admin_emails={"admin@example.com"},
            default_role=0) == 0

    def test_白名单邮箱拿到管理员全权限(self):
        assert oidc.resolve_new_user_role(
            "Admin@Example.com ", admin_emails={"admin@example.com"},
            default_role=0) == constants.ADMIN_USER_ROLES

    def test_默认角色原样透传(self):
        role = constants.ROLE_DOWNLOAD | constants.ROLE_VIEWER
        assert oidc.resolve_new_user_role(
            "reader@example.com", admin_emails=set(), default_role=role) == role

    def test_空邮箱不会命中白名单(self):
        role = oidc.resolve_new_user_role("", admin_emails={"", "a@b.c"}, default_role=3)
        assert role == 3

    def test_站点默认角色未初始化时按最小权限(self, monkeypatch):
        from cps import config
        monkeypatch.setattr(config, "config_default_role", None, raising=False)
        assert oidc.site_default_role() == 0
        assert oidc.resolve_new_user_role("x@y.z", admin_emails=set()) == 0

    def test_parse_admin_emails_去空格转小写忽略空项(self, monkeypatch):
        monkeypatch.setenv("OIDC_ADMIN_EMAILS", " A@B.com , ,c@d.com,, ")
        assert oidc.parse_admin_emails() == {"a@b.com", "c@d.com"}

    def test_白名单为空时无人获得管理员(self):
        assert oidc.resolve_new_user_role(
            "anyone@example.com", admin_emails=set(), default_role=0) == 0


class TestCallbackContract:
    """形制守卫：建号分支必须走决策函数，不能写死管理员角色。"""

    def test_建号处不再直写管理员角色(self):
        src = inspect.getsource(oidc.callback)
        assert "ADMIN_USER_ROLES" not in src, "回调不得再写死 ADMIN_USER_ROLES"
        assert src.count("role=resolve_new_user_role(email)") == 1

    def test_既有账号合并路径不赋值角色(self):
        """存量账号（OIDC subject 或 email 命中）只补绑定，不得动 role。"""
        src = inspect.getsource(oidc.callback)
        assert src.count("role=") == 1, "role= 只应出现在新建账号分支"


class TestAuditCli:
    @staticmethod
    def _make_db(path, default_role=0):
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE settings (id INTEGER PRIMARY KEY, config_default_role SMALLINT)")
        conn.execute("INSERT INTO settings (id, config_default_role) VALUES (1, ?)", (default_role,))
        conn.execute("CREATE TABLE user (id INTEGER PRIMARY KEY, name VARCHAR(64), "
                     "email VARCHAR(64), role SMALLINT, oidc_subject VARCHAR(255))")
        conn.executemany(
            "INSERT INTO user (id, name, email, role, oidc_subject) VALUES (?,?,?,?,?)",
            [(1, "admin", "admin@example.org", constants.ADMIN_USER_ROLES, None),
             (2, "selfreg", "newbie@example.com", constants.ADMIN_USER_ROLES, "sub-2"),
             (3, "reader", "reader@example.com", 0, "sub-3")])
        conn.commit()
        conn.close()

    def test_role_admin_常量与脚本内联值同源(self):
        assert audit.ROLE_ADMIN == constants.ROLE_ADMIN

    def test_清单标注是否经oidc登录(self, tmp_path):
        db = str(tmp_path / "app.db")
        self._make_db(db)
        conn = audit.connect_readonly(db)
        try:
            rows = audit.load_rows(conn)
            assert audit.load_default_role(conn) == 0
        finally:
            conn.close()
        by_id = {r["id"]: r for r in rows}
        assert by_id[1]["is_admin"] and not by_id[1]["via_oidc"]
        assert by_id[2]["is_admin"] and by_id[2]["via_oidc"]
        assert not by_id[3]["is_admin"]

    def test_降级必须点名(self, tmp_path):
        db = str(tmp_path / "app.db")
        self._make_db(db)
        with pytest.raises(ValueError):
            audit.plan_demotions([{"id": 2, "email": "a@b.c", "is_admin": True, "role": 479}])

    def test_默认角色含管理员位时拒绝降级(self):
        with pytest.raises(ValueError):
            audit.plan_demotions(
                [{"id": 2, "email": "a@b.c", "is_admin": True, "role": 479}],
                ids=[2], default_role=constants.ADMIN_USER_ROLES)

    def test_白名单账号受保护_已普通账号跳过(self):
        rows = [
            {"id": 1, "name": "admin", "email": "admin@example.com", "role": 479,
             "is_admin": True, "via_oidc": False},
            {"id": 2, "name": "newbie", "email": "newbie@example.com", "role": 479,
             "is_admin": True, "via_oidc": True},
            {"id": 3, "name": "reader", "email": "reader@example.com", "role": 0,
             "is_admin": False, "via_oidc": True},
        ]
        targets, skipped = audit.plan_demotions(
            rows, ids=[1, 2, 3], default_role=0,
            admin_emails={"admin@example.com"})
        assert [r["id"] for r in targets] == [2]
        reasons = {r["id"]: reason for r, reason in skipped}
        assert "白名单" in reasons[1]
        assert "本就不含管理员位" in reasons[3]

    def test_端到端降级写库并留备份(self, tmp_path, capsys, monkeypatch):
        db = str(tmp_path / "app.db")
        self._make_db(db)
        monkeypatch.delenv("OIDC_ADMIN_EMAILS", raising=False)
        assert audit.main(["--db", db, "--demote", "--ids", "2"]) == 0
        conn = sqlite3.connect(db)
        try:
            role = conn.execute("SELECT role FROM user WHERE id = 2").fetchone()[0]
            local_admin = conn.execute("SELECT role FROM user WHERE id = 1").fetchone()[0]
        finally:
            conn.close()
        assert role == 0, "自助注册账号应降为默认角色"
        assert local_admin == constants.ADMIN_USER_ROLES, "点名的本地管理员不受影响"
        backups = [p for p in os.listdir(str(tmp_path)) if ".r211-bak-" in p]
        assert len(backups) == 1, "写库前必须留一份备份"
        assert "已备份" in capsys.readouterr().out

    def test_dry_run_不写库(self, tmp_path, capsys):
        db = str(tmp_path / "app.db")
        self._make_db(db)
        assert audit.main(["--db", db, "--json", str(tmp_path / "admins.json")]) == 0
        conn = sqlite3.connect(db)
        try:
            role = conn.execute("SELECT role FROM user WHERE id = 2").fetchone()[0]
        finally:
            conn.close()
        assert role == constants.ADMIN_USER_ROLES
        assert (tmp_path / "admins.json").exists()
        assert "dry-run" in capsys.readouterr().out
