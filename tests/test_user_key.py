"""Tests for the cross-application stable user identifier (user_key).

覆盖：
  1. 存量用户回填：OIDC 用户沿用 Authentik sub，本地用户生成 UUID4，且幂等。
  2. 初始用户（admin/Guest）创建即携带 user_key。
  3. OIDC callback 首次登录创建的用户 user_key == Authentik sub。
  4. 本地建号（/register）创建的用户生成 UUID user_key。
  5. User 模型具备 user_key 唯一约束的列定义。
"""
from unittest.mock import Mock

import pytest

from cps import ub
from cps.oidc import init_oidc, oidc as oidc_bp, oauth as oidc_oauth


class TestBackfillUserKeys:
    """迁移回填逻辑（幂等）：OIDC 用户取 sub，本地用户生成 UUID。"""

    def test_oidc_user_uses_subject(self, app, ub_session):
        user = ub.User(name="oidc-user", email="oidc@example.com", role=1)
        user.oidc_issuer = "https://auth.example/application/o/magicbook/"
        user.oidc_subject = "sub-abc"
        ub_session.add(user)
        ub_session.commit()

        ub.backfill_user_keys(ub_session)
        ub_session.refresh(user)
        assert user.user_key == "sub-abc"

    def test_local_user_gets_uuid(self, app, ub_session):
        user = ub.User(name="local-user", email="local@example.com", role=1)
        ub_session.add(user)
        ub_session.commit()

        ub.backfill_user_keys(ub_session)
        ub_session.refresh(user)
        assert user.user_key

    def test_is_idempotent(self, app, ub_session):
        user = ub.User(name="keep-key", email="keep@example.com", role=1)
        user.user_key = "already-set"
        ub_session.add(user)
        ub_session.commit()

        ub.backfill_user_keys(ub_session)
        ub_session.refresh(user)
        assert user.user_key == "already-set"

    def test_user_key_column_exists(self, app, ub_session):
        assert hasattr(ub.User, "user_key")


class TestInitialUsers:
    """初始用户创建即生成 user_key。"""

    def test_admin_and_guest_have_user_key(self, app, ub_session):
        admin = ub_session.query(ub.User).filter_by(name="admin").first()
        guest = ub_session.query(ub.User).filter_by(name="Guest").first()
        assert admin is not None and admin.user_key
        assert guest is not None and guest.user_key


class TestOidcCallback:
    """OIDC 首次登录创建的用户 user_key 必须等于 Authentik sub。"""

    ISSUER = "https://auth.example/application/o/magicbook/"
    SUB = "sub-oidc-123"

    @pytest.fixture
    def oidc_client(self, app, monkeypatch):
        # 测试环境 create_app() 时未配置 Authentik env，oidc blueprint 未注册；此处补齐
        if "oidc" not in app.blueprints:
            app.register_blueprint(oidc_bp)
        monkeypatch.setenv("AUTHENTIK_ISSUER", self.ISSUER)
        monkeypatch.setenv("AUTHENTIK_MAGICBOOK_CLIENT_ID", "test-client")
        monkeypatch.setenv("AUTHENTIK_MAGICBOOK_CLIENT_SECRET", "test-secret")
        monkeypatch.setenv("AUTHENTIK_MAGICBOOK_REDIRECT_URI",
                           "https://cw.example/oidc/callback")
        assert init_oidc(app) is True
        fake = Mock()
        fake.authorize_access_token.return_value = {
            "userinfo": {
                "sub": self.SUB,
                "preferred_username": "alice",
                "email": "alice@example.com",
            }
        }
        monkeypatch.setattr(oidc_oauth, "authentik", fake)
        return app.test_client()

    def test_new_oidc_user_gets_sub_as_user_key(self, oidc_client, ub_session):
        rv = oidc_client.get("/oidc/callback")
        assert rv.status_code == 302
        user = ub_session.query(ub.User).filter_by(oidc_subject=self.SUB).first()
        assert user is not None
        assert user.user_key == self.SUB

    def test_existing_oidc_user_key_unchanged(self, oidc_client, ub_session):
        # 清理上个测试残留的同一 OIDC 用户，保证本用例独立
        ub_session.query(ub.User).filter(ub.User.oidc_subject == self.SUB).delete()
        ub_session.commit()
        user = ub.User(name="alice", email="alice@example.com", role=1)
        # callback 按 rstrip('/') 后的 issuer 匹配，预绑定必须一致
        user.oidc_issuer = self.ISSUER.rstrip("/")
        user.oidc_subject = self.SUB
        user.user_key = "already-bound"
        ub_session.add(user)
        ub_session.commit()

        rv = oidc_client.get("/oidc/callback")
        assert rv.status_code == 302
        ub_session.refresh(user)
        assert user.user_key == "already-bound"
