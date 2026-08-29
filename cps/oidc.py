import os
import requests
from urllib.parse import urljoin

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, redirect, request, session, url_for, flash
from . import ub, log, constants
from .cw_login import login_user


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
    user = ub.session.query(ub.User).filter(ub.User.oidc_issuer == issuer, ub.User.oidc_subject == subject).first()
    if user is None:
        # Never merge an existing local account silently by username or email.
        # An administrator can link accounts explicitly later if required.
        user = ub.User(name=username, email=userinfo.get("email", ""), role=constants.ADMIN_USER_ROLES)
        user.oidc_issuer = issuer
        user.oidc_subject = subject
        ub.session.add(user)
        ub.session.commit()
    login_user(user, remember=True)
    if id_token and constants.MOON_WELL_READING_URL:
        try:
            response = requests.post(
                constants.MOON_WELL_READING_URL.rstrip("/") + "/auth/oidc/exchange",
                json={"idToken": id_token}, timeout=8)
            response.raise_for_status()
            moonwell_result = response.json().get("result", {})
            if moonwell_result.get("accessToken"):
                session["moonwell_access_token"] = moonwell_result["accessToken"]
            if moonwell_result.get("refreshToken"):
                session["moonwell_refresh_token"] = moonwell_result["refreshToken"]
        except requests.RequestException as error:
            log.warning("moon-well OIDC token exchange failed: %s", error)
    return redirect(session.pop("oidc_next", url_for("web.index")))
