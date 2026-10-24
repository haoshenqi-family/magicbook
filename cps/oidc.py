import base64
import json
import os
import requests
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit

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
from .landing import landing_endpoint
from .redirect import get_redirect_location
from .cw_babel import get_available_translations


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


def site_default_role():
    """OIDC 自助注册新账号的角色＝站点「新用户默认角色」（管理后台 → 编辑基本设置）。

    Why：2026-10-23 用户拍板「默认都是普通用户，管理员用户由我手动赋予」——
        自助注册链路上不再存在任何自动提权路径，管理员只能由人在管理后台
        逐个赋予。因此即便站点默认角色被勾上管理员位，这里也强制剔除。
    How：oidc.py 与 cps/__init__ 存在循环导入风险（config 单例在包初始化后段
        才创建），故延迟导入；配置未初始化（None）时按最小权限 0
        （＝普通读者，不含任何角色位）返回。
    """
    from . import config

    role = getattr(config, "config_default_role", None)
    role = 0 if role is None else int(role)
    if constants.has_flag(role, constants.ROLE_ADMIN):
        role &= ~constants.ROLE_ADMIN
        log.warning("站点默认角色含管理员位，已剔除：OIDC 自助注册一律为普通用户，"
                    "管理员需在管理后台手动赋予")
    return role


def resolve_new_user_role():
    """OIDC 自助注册新账号的角色决策（R211，缺陷根因修复点）。

    旧实现在建号处写死 ``constants.ADMIN_USER_ROLES``（含 ``ROLE_ADMIN``），
    任何拿到公开邀请链接的人首次登录即成为超管。现在统一走站点默认角色，
    且该角色已被 ``site_default_role()`` 剔除管理员位。
    """
    return site_default_role()


def _normalize_locale(value):
    """把 OIDC claim / Accept-Language 归一成本站实际存在的 gettext locale。

    Why：Authentik 常见 claim 是 ``zh-CN`` 或 ``zh-Hans-CN``，而本站翻译目录
    与 ``user.locale`` 使用的是 ``zh_Hans_CN``。直接落库会让 Babel 找不到翻译，
    界面静默退回英文；直接接受任意 claim 又可能写入不存在的目录。
    How：先按 Babel 规范化，再以完整 locale → 语言+地区 → 语言+文字 → 语言
    逐级回退。只接受 ``cps/translations`` 里真实存在的 locale，失败返回 None。
    """
    from babel import Locale
    from babel.core import UnknownLocaleError

    raw = (value or "").strip()
    if not raw:
        return None
    try:
        locale = Locale.parse(raw.replace("-", "_"))
    except (UnknownLocaleError, ValueError):
        return None

    candidates = []
    if locale.language and locale.script and locale.territory:
        candidates.append("{0}_{1}_{2}".format(
            locale.language, locale.script, locale.territory))
    if locale.language and locale.territory:
        candidates.append("{0}_{1}".format(locale.language, locale.territory))
    if locale.language and locale.script:
        candidates.append("{0}_{1}".format(locale.language, locale.script))
    if locale.language:
        candidates.append(locale.language)
    try:
        available = get_available_translations()
    except (RuntimeError, KeyError):
        # 纯函数层（无 app 上下文）不依赖 Flask-Babel；生产请求内会在下面
        # 按真实翻译目录过滤，避免写入不存在的 locale。
        return candidates[0] if candidates else None
    for candidate in candidates:
        if candidate in available:
            return candidate
    return None


def new_user_locale(claims):
    """新账号初始 locale：Authentik locale claim > Accept-Language > 站点默认值。

    Why 只用于新建账号：已有账号的语言是用户显式偏好，不能在每次 OIDC 登录时
    被浏览器头覆盖。Accept-Language 使用 Werkzeug 的 quality 排序结果，避免自己
    解析 q 值；claim 不允许时继续看浏览器，而不是强行写英文。
    """
    from . import config

    claim_locale = _normalize_locale((claims or {}).get("locale"))
    if claim_locale:
        return claim_locale

    preferred = []
    for value in request.accept_languages.values():
        normalized = _normalize_locale(value)
        if normalized and normalized not in preferred:
            preferred.append(normalized)
    if preferred:
        return preferred[0]

    return _normalize_locale(getattr(config, "config_default_locale", None)) or "en"


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
    # R213-C：登录入口没带 next 时落站点默认落点（/home 或原 / 发现页）；
    # 这里存的是完整 URL，callback 直接 302，故用 url_for 而非 endpoint 名。
    session["oidc_next"] = request.args.get("next") or url_for(landing_endpoint())
    return oauth.authentik.authorize_redirect(redirect_uri)


def _invite_token():
    """从 ``AUTHENTIK_ENROLLMENT_INVITE_URL`` 解析出邀请 token（itoken）。

    Why：沿用既有配置而不新增 env 变量——避免「invite URL 与 invite token 两份
        配置各自漂移」，轮换时仍只改一个地方。Authentik 只解析外层 ``query``
        参数的整段值，因此当前正确形态是
        ``.../?query=itoken%3D<uuid>``；同时兼容老式顶层 ``?itoken=<uuid>``，
        避免升级瞬间把既有部署的注册入口关掉。
    How：先解析外层 ``query`` 里的嵌套 query，再回退解析顶层 query；两种位置
        都兼容 ``itoken`` / ``token`` 两种 key。解析不出返回 None（调用方据此
        关闭注册入口，不静默跳坏链接）。
    """
    raw = (os.getenv("AUTHENTIK_ENROLLMENT_INVITE_URL") or "").strip()
    if not raw:
        return None

    outer_query = parse_qs(urlsplit(raw).query, keep_blank_values=True)
    nested_queries = outer_query.get("query") or []
    for nested_query in nested_queries:
        nested = parse_qs(nested_query, keep_blank_values=True)
        for key in ("itoken", "token"):
            value = (nested.get(key) or [""])[0].strip()
            if value:
                return value

    # 向后兼容 R103 以来的顶层 query；Authentik 新版本不再读取这一层。
    for key in ("itoken", "token"):
        value = (outer_query.get(key) or [""])[0].strip()
        if value:
            return value
    return None


def _signup_authorize_target(redirect_uri):
    """构造「注册完成后回 magicbook」的 OIDC 授权跳转目标（Authentik 同域相对路径）。

    Why：Authentik 的 flow 结束时从 session 取 ``next`` 跳走，而 ``next``
        **只接受相对路径**（``executor._flow_done()`` 用 ``is_url_absolute()``
        判定，带 netloc 会被拒为 "Invalid next URL"）。因此不能把
        ``https://magicbook.haoshenqi.top/oidc/callback`` 直接塞进 next。
        办法是让 next 指向 **Authentik 自己的授权端点**——它与 flow 同域，
        可写成相对路径 ``/application/o/authorize/?...``。Authentik 此时已由
        邀请 flow 末位的 UserLoginStage 建立登录态，会静默签发 code 并 302 回
        magicbook 的 redirect_uri。magicbook 侧的 callback() 逻辑完全复用，
        建号/绑号/角色判定不分叉。
    How：authlib 生成授权 URL（含 state/nonce/PKCE）→ 剥掉 scheme+host 只留
        path+query → 作为 next。state 等参数由 authlib 写入 Flask session，
        与既有 /oidc/login 路径完全一致。
    """
    rv = oauth.authentik.create_authorization_url(redirect_uri)
    # authlib 把 state/nonce/code_verifier 存入 session，回调时凭 state 取回
    oauth.authentik.save_authorize_data(redirect_uri=redirect_uri, **rv)
    parts = urlsplit(rv["url"])
    if parts.scheme or parts.netloc:
        # 同域相对路径：Authentik 的 next 硬约束要求不能带 netloc
        return urlunsplit(("", "", parts.path, parts.query, ""))
    return rv["url"]


@oidc.get("/signup")
def signup():
    """注册入口：把 Authentik 邀请注册 flow 与 OIDC 授权串成一条链。

    Why：R103 起注册按钮直连邀请 flow（``target="_blank``），用户注册完停在
        Authentik 侧，必须切回 magicbook 再点一次「Log in」——注册与登录断开。
        本端点把两者串起来：先在 magicbook 侧生成 OIDC 授权 URL（state 存
        session），再把它作为 ``next`` 挂在邀请 flow 后面；用户在 Authentik
        完成注册后，flow 直接跳到授权端点静默签发 code，回到 magicbook 时
        **已经是登录态**，无需二次点击。
    How：授权 URL 的 path+query 作为 next（相对路径，见
        ``_signup_authorize_target``）；itoken 从既有 env 解析；用户指定的
        「注册完回哪个页面」走 ``get_redirect_location`` 做站内校验。
    """
    if not current_app.config.get("AUTHENTIK_OIDC_ENABLED"):
        flash("Authentik OIDC is not configured", "error")
        return redirect(url_for("web.login"))

    invite_token = _invite_token()
    if not invite_token:
        flash("Registration is temporarily unavailable", "error")
        return redirect(url_for("web.login"))

    redirect_uri = os.getenv("AUTHENTIK_MAGICBOOK_REDIRECT_URI") or url_for("oidc.callback", _external=True)
    try:
        target = _signup_authorize_target(redirect_uri)
    except Exception as exc:
        log.error("OIDC signup: failed to build authorization URL: %s", exc)
        flash("Registration is temporarily unavailable", "error")
        return redirect(url_for("web.login"))

    # 注册完成后回到 magicbook 的哪个页面（只允许站内相对路径）
    # R213-C：默认落点跟随站点配置（/home 或原 / 发现页），不再写死 web.index——
    # 否则「注册即登录」会与本地登录落点不一致（新用户注册完被扔回老首页）。
    session["oidc_next"] = get_redirect_location(request.args.get("next"), landing_endpoint())

    invite_base = (os.getenv("AUTHENTIK_ENROLLMENT_INVITE_URL") or "").strip()
    parts = urlsplit(invite_base)
    flow_path = parts.path or "/if/flow/invitation-enrollment/"
    # Authentik executor 只解析外层 query 参数的整段值：
    # get_params = QueryDict(request.GET.get("query", ""))。因此 itoken 与 next
    # 必须先组成内层 query，再整体作为外层 query 参数编码（否则会被判 Invalid invite）。
    nested_query = urlencode({"itoken": invite_token, "next": target})
    flow_query = urlencode({"query": nested_query})
    signup_url = urlunsplit((parts.scheme, parts.netloc, flow_path, flow_query, ""))
    log.info("OIDC signup: redirect to invitation enrollment flow (flow=%s)", flow_path)
    return redirect(signup_url)


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
            # R211：自助注册不再继承管理员权限——一律站点默认角色（已剔除管理员位），
            # 管理员由人在管理后台手动赋予（2026-10-23 用户拍板）。
            user = ub.User(name=username, email=email,
                          role=resolve_new_user_role(),
                          locale=new_user_locale(userinfo))
            ub.session.add(user)
        user.oidc_issuer = issuer
        user.oidc_subject = subject
        ub.session.commit()
    login_user(user, remember=True)

    # 用 Authentik id_token 向 moon-well 换取 access_token，
    # 存入 session 供阅读器代理接口透传 Authorization: Bearer。
    log.info("OIDC callback: id_token present=%s, moonwell_url=%s",
             bool(id_token), os.getenv("MOON_WELL_READING_URL", ""))
    if id_token:
        # R178（架构评审 B1）：exchange 直连收编 cps/moonwell/client（URL、禁代理、
        # accessToken/refreshToken 双键名解析口径单点化，回调页不再自连）
        from cps.moonwell.client import client

        try:
            access_token, refresh_token = client.exchange_id_token(id_token)
            if access_token:
                session["moonwell_access_token"] = access_token
            if refresh_token:
                session["moonwell_refresh_token"] = refresh_token
            if not access_token:
                log.warning("moon-well token exchange failed")
            else:
                log.info("moon-well token exchange OK: token_len=%d", len(access_token))
        except Exception as exc:
            log.warning("moon-well token exchange error: %s", exc)

    # R213-C：oidc_next 丢失时也走站点默认落点（同样受 config_home_landing 控制）
    return redirect(session.pop("oidc_next", url_for(landing_endpoint())))
