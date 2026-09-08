import base64
import json
import os
import requests
from urllib.parse import urljoin

from authlib.integrations.flask_client import OAuth
from authlib.integrations.flask_client.apps import FlaskOAuth2App
from authlib.jose import jwt as jose_jwt
from authlib.oidc.core import CodeIDToken, ImplicitIDToken, UserInfo
from flask import Blueprint, current_app, redirect, request, session, url_for, flash
from joserfc import jwt as jose_rfc_jwt
from joserfc.jwk import KeySet
from joserfc.jws import JWSRegistry
from sqlalchemy import func
from . import ub, log, constants
from .cw_login import login_user


class AuthentikOAuth2App(FlaskOAuth2App):
    """FlaskOAuth2App 子类，兼容 authentik 使用 HS256 签名的 id_token。

    authentik 若配置 RSA 签名，其 jwks_uri 正常返回公钥，走 authlib 默认的
    JWKS 公钥校验路径即可。但若配置为对称签名（HS256），jwks_uri 返回空对象
    {}（对称密钥不会通过 JWKS 发布）。新版 authlib 的 parse_id_token 会在解码
    前急加载 JWKS（``KeySet.import_key_set``），空对象必然抛 ``KeyError: 'keys'``
    并导致 /oidc/callback 返回 500。因此这里重写 parse_id_token：当 id_token 的
    算法是 HS* 对称签名时，直接以 client_secret 作为 HMAC 校验密钥；RS*/其他
    非对称算法仍走默认 JWKS 路径。
    """

    @staticmethod
    def _id_token_algorithm(id_token):
        """稳妥解析 id_token 的 JOSE header 中的 alg，失败时回退为 RS256。"""
        try:
            header_segment = id_token.split(".")[0]
            header = json.loads(base64.urlsafe_b64decode(header_segment + "=="))
            return (header.get("alg") or "").upper()
        except Exception:
            return "RS256"

    def parse_id_token(self, token, nonce=None, claims_options=None,
                       claims_cls=None, leeway=120):
        if "id_token" not in token:
            return None

        claims_params = dict(nonce=nonce, client_id=self.client_id)
        if claims_cls is None:
            if "access_token" in token:
                claims_params["access_token"] = token["access_token"]
                claims_cls = CodeIDToken
            else:
                claims_cls = ImplicitIDToken

        metadata = self.load_server_metadata()
        if claims_options is None and "issuer" in metadata:
            claims_options = {"iss": {"values": [metadata["issuer"]]}}

        alg_values = metadata.get("id_token_signing_alg_values_supported")
        id_token = token["id_token"]

        alg = self._id_token_algorithm(id_token)
        if alg.startswith("HS") and self.client_secret:
            # 对称签名（HS256/HS384/HS512）：动作是 HMAC，密钥为 client_secret，
            # 不能从空的 JWKS 取公钥。authlib.jose 直接接受字符串密钥，且其
            # decode 返回的就是 claims 对象本身（含 .header）。
            decoded = jose_jwt.decode(id_token, self.client_secret)
            claims_data, header = decoded, decoded.header
        else:
            key = KeySet.import_key_set(self.fetch_jwk_set())
            decoded = jose_rfc_jwt.decode(
                id_token,
                key=key,
                registry=JWSRegistry(algorithms=alg_values, strict_check_header=False),
            )
            claims_data, header = decoded.claims, decoded.header
        claims = claims_cls(claims_data, header, claims_options, claims_params)
        if claims.get("nonce_supported") is False:
            claims.params["nonce"] = None
        claims.validate(leeway=leeway)
        return UserInfo(claims)


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
    id_token = token.get("id_token")
    userinfo = token.get("userinfo") or oauth.authentik.userinfo()
    subject = userinfo.get("sub")
    if not subject:
        flash("Authentik did not return a subject", "error")
        return redirect(url_for("web.login"))
    issuer = os.getenv("AUTHENTIK_ISSUER", "").rstrip("/")
    username = userinfo.get("preferred_username") or userinfo.get("email") or "oidc-" + subject
    email = (userinfo.get("email") or "").strip()
    user = ub.session.query(ub.User).filter(ub.User.oidc_issuer == issuer, ub.User.oidc_subject == subject).first()
    if user is None:
        # 兼容存量本地账号：已绑定过该 subject 则复用；否则按 email 精确匹配既有
        # 本地 Calibre 账号并补绑 OIDC（保留其本地角色/书库权限），与 moon-well 的
        # upsertUser 合并策略一致，达成真正的同一套账户体系。
        if email:
            user = ub.session.query(ub.User).filter(
                func.lower(ub.User.email) == email.lower()).first()
        if user is None:
            user = ub.User(name=username, email=email, role=constants.ADMIN_USER_ROLES)
            ub.session.add(user)
        user.oidc_issuer = issuer
        user.oidc_subject = subject
        ub.session.commit()
    login_user(user, remember=True)

    # 用 Authentik id_token 向 moon-well 换取 access_token，
    # 存入 session 供阅读器代理接口透传 Authorization: Bearer。
    if id_token:
        moonwell_url = os.getenv("MOON_WELL_READING_URL", "").rstrip("/")
        if moonwell_url:
            try:
                resp = requests.post(
                    moonwell_url + "/auth/oidc/exchange",
                    json={"id_token": id_token},
                    timeout=8,
                    proxies={"http": None, "https": None},
                )
                if resp.ok:
                    data = resp.json()
                    result = data.get("result") or {}
                    access_token = result.get("accessToken") or result.get("access_token")
                    refresh_token = result.get("refreshToken") or result.get("refresh_token")
                    if access_token:
                        session["moonwell_access_token"] = access_token
                    if refresh_token:
                        session["moonwell_refresh_token"] = refresh_token
            except Exception:
                pass  # 交换失败不阻断登录，阅读功能降级为不可用

    return redirect(session.pop("oidc_next", url_for("web.index")))
