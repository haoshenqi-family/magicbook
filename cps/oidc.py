import os
from urllib.parse import urljoin

from authlib.integrations.flask_client import OAuth
from authlib.integrations.flask_client.apps import FlaskOAuth2App
from authlib.jose import JsonWebKey
from flask import Blueprint, current_app, redirect, request, session, url_for, flash
from . import ub, log
from .cw_login import login_user


class AuthentikOAuth2App(FlaskOAuth2App):
    """FlaskOAuth2App 子类，兼容 authentik 使用 HS256 签名的 id_token。

    authentik 若配置 RSA 签名，其 jwks_uri 正常返回公钥，走 authlib 默认的
    JWKS 公钥校验路径即可。但若配置为对称签名（HS256），jwks_uri 返回空对象
    {}（对称密钥不会通过 JWKS 发布），authlib 的 parse_id_token 会因
    ``import_key_set({})`` 抛出 ``ValueError: Invalid key set format`` 并导致
    /oidc/callback 返回 500。此时 id_token 由 client_secret 做 HMAC 对称签名，
    应以 client_secret 作为校验密钥；RS*/其他算法仍回退到默认 JWKS 路径。
    """

    def create_load_key(self):
        def load_key(header, payload):
            alg = (header.get("alg") or "").upper()
            if alg.startswith("HS"):
                return self.client_secret
            jwk_set = JsonWebKey.import_key_set(self.fetch_jwk_set())
            try:
                return jwk_set.find_by_kid(header.get("kid"))
            except ValueError:
                # 重试强制刷新 JWKS，兼容首次缓存为空等场景
                jwk_set = JsonWebKey.import_key_set(self.fetch_jwk_set(force=True))
                return jwk_set.find_by_kid(header.get("kid"))

        return load_key


oidc = Blueprint("oidc", __name__, url_prefix="/oidc")
oauth = OAuth()


def init_oidc(app):
    issuer = os.getenv("AUTHENTIK_ISSUER", "").rstrip("/")
    client_id = os.getenv("AUTHENTIK_MAGICBOOK_CLIENT_ID", "")
    client_secret = os.getenv("AUTHENTIK_MAGICBOOK_CLIENT_SECRET", "")
    if not issuer or not client_id or not client_secret:
        return False
    oauth.init_app(app)
    oauth.register(
        name="authentik",
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url=urljoin(issuer + "/", ".well-known/openid-configuration"),
        client_kwargs={"scope": "openid profile email"},
        client_cls=AuthentikOAuth2App,
    )
    app.config["AUTHENTIK_OIDC_ENABLED"] = True
    return True


@oidc.get("/login")
def login():
    if not current_app.config.get("AUTHENTIK_OIDC_ENABLED"):
        flash("Authentik OIDC is not configured", "error")
        return redirect(url_for("web.login"))
    redirect_uri = os.getenv("AUTHENTIK_MAGICBOOK_REDIRECT_URI") or url_for("oidc.callback", _external=True)
    session["oidc_next"] = request.args.get("next") or url_for("web.index")
    return oauth.authentik.authorize_redirect(redirect_uri)


@oidc.get("/callback")
def callback():
    token = oauth.authentik.authorize_access_token()
    userinfo = token.get("userinfo") or oauth.authentik.userinfo()
    subject = userinfo.get("sub")
    if not subject:
        flash("Authentik did not return a subject", "error")
        return redirect(url_for("web.login"))
    issuer = os.getenv("AUTHENTIK_ISSUER", "").rstrip("/")
    username = userinfo.get("preferred_username") or userinfo.get("email") or "oidc-" + subject
    user = ub.session.query(ub.User).filter(ub.User.oidc_issuer == issuer, ub.User.oidc_subject == subject).first()
    if user is None:
        # Never merge an existing local account silently by username or email.
        # An administrator can link accounts explicitly later if required.
        user = ub.User(name=username, email=userinfo.get("email", ""), role=1)
        user.oidc_issuer = issuer
        user.oidc_subject = subject
        ub.session.add(user)
        ub.session.commit()
    login_user(user, remember=True)
    return redirect(session.pop("oidc_next", url_for("web.index")))
