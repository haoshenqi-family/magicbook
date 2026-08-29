"""Tests for the Authentik OIDC login flow (cps/oidc.py).

覆盖场景：authentik 若以 HS256 对 id_token 对称签名，jwks_uri 返回空对象
{}，authlib 默认的 JWKS 公钥校验会抛 ``ValueError: Invalid key set format``
并导致 /oidc/callback 返回 500。AuthentikOAuth2App 应改用 client_secret
作为 HMAC 校验密钥；RS256 等非对称算法仍走原 JWKS 路径。
"""
import json
import time

import pytest
from authlib.common.encoding import urlsafe_b64encode
from authlib.integrations.flask_client import OAuth
from authlib.integrations.flask_client.apps import FlaskOAuth2App
from authlib.jose import JsonWebKey
from authlib.jose import jwt as jose_jwt

from cps.oidc import AuthentikOAuth2App, init_oidc

CLIENT_ID = "test-client"
CLIENT_SECRET = "test-secret"
ISSUER = "https://auth.example/application/o/magicbook/"


def _build_id_token(algorithm, signing_key, *, sub="user-123", nonce="nonce-123"):
    """构造一个合法签名的 id_token，供 parse_id_token 校验使用。"""
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "sub": sub,
        "aud": CLIENT_ID,
        "exp": now + 3600,
        "iat": now,
        "nonce": nonce,
        "preferred_username": "alice",
    }
    header = {"alg": algorithm, "typ": "JWT"}
    if isinstance(signing_key, dict):
        header["kid"] = signing_key.get("kid")
    return jose_jwt.encode(header, claims, signing_key).decode()


def _make_client(app, client_cls, alg_values, jwk_set):
    """注册一个 authentik OAuth 客户端，预置 server_metadata 与 JWKS。"""
    oauth = OAuth()
    oauth.init_app(app)
    oauth.register(
        name="authentik",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        server_metadata_url=ISSUER + ".well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
        client_cls=client_cls,
    )
    client = oauth.create_client("authentik")
    client.server_metadata.update({
        "_loaded_at": time.time(),
        "issuer": ISSUER,
        "jwks_uri": ISSUER + "jwks/",
        "jwks": jwk_set,
        "id_token_signing_alg_values_supported": alg_values,
    })
    # 避免真实网络请求：直接返回预置的 JWKS 内容
    client.fetch_jwk_set = lambda force=False: jwk_set
    return client


class TestAuthentikOAuth2App:
    def test_hs256_id_token_verifies_with_client_secret(self, app):
        """HS256 + 空 JWKS 时，AuthentikOAuth2App 用 client_secret 完成校验。"""
        client = _make_client(app, AuthentikOAuth2App, ["HS256"], jwk_set={})
        token = _build_id_token("HS256", CLIENT_SECRET)
        userinfo = client.parse_id_token({"id_token": token}, nonce="nonce-123")
        assert userinfo["sub"] == "user-123"
        assert userinfo["preferred_username"] == "alice"

    def test_tampered_hs256_id_token_is_rejected(self, app):
        """篡改过的 id_token 即使算法为 HS256 也必须校验失败。"""
        client = _make_client(app, AuthentikOAuth2App, ["HS256"], jwk_set={})
        token = _build_id_token("HS256", CLIENT_SECRET)
        # 复用头部与签名，仅替换为篡改过的 payload → HMAC 校验必须失败
        header_b64, _, signature_b64 = token.split(".")
        tampered_payload = json.dumps({
            "iss": ISSUER, "sub": "evil-user", "aud": CLIENT_ID,
            "exp": int(time.time()) + 3600, "iat": int(time.time()),
            "nonce": "nonce-123",
        }).encode("utf-8")
        tampered = header_b64 + "." + urlsafe_b64encode(tampered_payload).decode() + "." + signature_b64
        with pytest.raises(Exception):
            client.parse_id_token({"id_token": tampered}, nonce="nonce-123")

    def test_rs256_id_token_still_uses_jwks(self, app):
        """RS256 + 正常 JWKS 时仍走原公钥校验路径（回归保护）。"""
        private = JsonWebKey.generate_key("RSA", 2048, is_private=True,
                                          options={"kid": "test-kid"})
        private_jwk = private.as_dict(is_private=True)
        public_jwk = {k: v for k, v in private_jwk.items()
                      if k not in ("d", "p", "q", "dp", "dq", "qi")}
        client = _make_client(app, AuthentikOAuth2App, ["RS256"],
                              jwk_set={"keys": [public_jwk]})
        token = _build_id_token("RS256", private_jwk)
        userinfo = client.parse_id_token({"id_token": token}, nonce="nonce-123")
        assert userinfo["sub"] == "user-123"

    def test_default_app_fails_on_hs256_with_empty_jwks(self, app):
        """回归对照：默认 FlaskOAuth2App 在 HS256 + 空 JWKS 下必然抛错。"""
        client = _make_client(app, FlaskOAuth2App, ["HS256"], jwk_set={})
        token = _build_id_token("HS256", CLIENT_SECRET)
        with pytest.raises(ValueError):
            client.parse_id_token({"id_token": token}, nonce="nonce-123")


class TestInitOidc:
    def test_noop_without_config(self, app, monkeypatch):
        """未配置环境变量时 init_oidc 应静默返回 False。"""
        monkeypatch.delenv("AUTHENTIK_ISSUER", raising=False)
        monkeypatch.delenv("AUTHENTIK_MAGICBOOK_CLIENT_ID", raising=False)
        monkeypatch.delenv("AUTHENTIK_MAGICBOOK_CLIENT_SECRET", raising=False)
        assert init_oidc(app) is False

    def test_registers_custom_app_when_configured(self, app, monkeypatch):
        """配置齐全时注册的客户端必须是 AuthentikOAuth2App。"""
        monkeypatch.setenv("AUTHENTIK_ISSUER", ISSUER)
        monkeypatch.setenv("AUTHENTIK_MAGICBOOK_CLIENT_ID", CLIENT_ID)
        monkeypatch.setenv("AUTHENTIK_MAGICBOOK_CLIENT_SECRET", CLIENT_SECRET)
        monkeypatch.setenv("AUTHENTIK_MAGICBOOK_REDIRECT_URI",
                           "https://cw.example/oidc/callback")
        from cps.oidc import oauth
        try:
            assert init_oidc(app) is True
            assert app.config.get("AUTHENTIK_OIDC_ENABLED") is True
            client = oauth.create_client("authentik")
            assert isinstance(client, AuthentikOAuth2App)
        finally:
            # app 是会话级共享实例：不清掉该标志会让后续用例渲染 /login 时
            # 走到未注册的 oidc.login 端点，url_for 抛 BuildError
            app.config.pop("AUTHENTIK_OIDC_ENABLED", None)
