"""Authentik OAuth2 login provider for calibre-web.

Uses flask-dance's generic OAuth2ConsumerBlueprint (flask-dance is already an
optional dependency) to support Authentik as an OAuth2/OIDC provider. Authentik
follows standard OAuth2 endpoints:
  authorize:  /application/o/authorize/
  token:      /application/o/token/
  userinfo:   /application/o/userinfo/

The blueprint is registered only if an ``authentik`` AiProvider row exists and
is active. Tokens are stored in the existing ``ub.OAuth`` table (same as
github/google) so the existing ``bind_oauth_or_register()`` flow handles user
linking.

Config is stored in the AiProvider table:
  api_base          -> Authentik application base URL
  api_key_encrypted -> client_id (encrypted, reuses the same field)
  models_json       -> JSON with {"client_secret_encrypted": "..."} (storing
                       the secret; slight abuse of models_json to avoid a new
                       column and keep the schema stable.)

This module is self-contained: it does NOT modify cps/oauth_bb.py.
"""
import json
import os
import logging

from flask import redirect, url_for, flash
from flask_babel import gettext as _

# flask-dance / oauthlib are optional (Authentik OAuth). Guard the imports so
# this module can be imported — and the rest of the AI package load — even when
# they are not installed. register_authentik() becomes a no-op in that case.
try:
    from flask_dance.consumer import oauth_authorized
    from flask_dance.consumer.oauth2 import OAuth2ConsumerBlueprint
    from oauthlib.oauth2 import TokenExpiredError, InvalidGrantError
    _FLASK_DANCE_AVAILABLE = True
except ImportError:
    oauth_authorized = None
    OAuth2ConsumerBlueprint = None
    TokenExpiredError = InvalidGrantError = Exception
    _FLASK_DANCE_AVAILABLE = False

from cps import ub, logger
from cps.cw_login import current_user
from cps.usermanagement import user_login_required

from .models import AiProvider
from .crypto import decrypt_value

log = logging.getLogger("cps.ai.authentik")

_AUTHENTIK_BLUEPRINT = None


def _get_encryption_key():
    """Get the Fernet key calibre-web uses for config secrets."""
    from cps.config_sql import get_encryption_key
    settings_path = os.path.dirname(ub.app_DB_path)
    key, _ = get_encryption_key(settings_path)
    return key or b""


def _get_authentik_config():
    """Return (client_id, client_secret, base_url) or None if not configured."""
    try:
        from .database import get_session
        sess = get_session()
        prov = sess.query(AiProvider).filter_by(
            provider_name="authentik", active=True).first()
        if prov is None or not prov.api_base:
            return None
        key = _get_encryption_key()
        client_id = decrypt_value(prov.api_key_encrypted, key)
        client_secret = ""
        try:
            extra = json.loads(prov.models_json or "{}")
            if isinstance(extra, dict):
                client_secret = decrypt_value(
                    extra.get("client_secret_encrypted", ""), key)
        except (json.JSONDecodeError, TypeError):
            pass
        return client_id, client_secret, prov.api_base
    except Exception as e:
        log.warning("authentik config read failed: %s", e)
        return None


def register_authentik(flask_app):
    """Register the Authentik OAuth2 blueprint if configured.

    Called from cps/main.py. Safe to call when authentik is not configured or
    flask-dance is not installed — it will be a no-op.
    """
    if not _FLASK_DANCE_AVAILABLE:
        log.info("flask-dance not installed, skipping Authentik OAuth registration")
        return
    global _AUTHENTIK_BLUEPRINT
    config = _get_authentik_config()
    if config is None:
        log.info("Authentik OAuth not configured, skipping blueprint registration")
        return

    client_id, client_secret, base_url = config
    base_url = base_url.rstrip("/")

    blueprint = OAuth2ConsumerBlueprint(
        "authentik",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        base_url=base_url + "/",
        authorization_url=base_url + "/authorize/",
        token_url=base_url + "/token/",
        scope=["openid", "email", "profile"],
        redirect_to="authentik.login_authentik",
    )

    # Ensure an OAuthProvider row exists for authentik (needed by OAuthBackend)
    sess = ub.session
    oauth_prov = sess.query(ub.OAuthProvider).filter_by(
        provider_name="authentik").first()
    if oauth_prov is None:
        oauth_prov = ub.OAuthProvider()
        oauth_prov.provider_name = "authentik"
        oauth_prov.active = True
        sess.add(oauth_prov)
        sess.commit()

    # Use calibre-web's OAuthBackend for token storage
    try:
        from cps.oauth import OAuthBackend
        blueprint.backend = OAuthBackend(
            ub.OAuth, sess, str(oauth_prov.id),
            user=current_user, user_required=True)
    except Exception as e:
        log.warning("authentik backend setup failed: %s", e)

    flask_app.register_blueprint(blueprint, url_prefix="/login")
    _AUTHENTIK_BLUEPRINT = blueprint

    @oauth_authorized.connect_via(blueprint)
    def authentik_logged_in(bp, token):
        if not token:
            flash(_("Failed to log in with Authentik."), category="error")
            return False
        resp = bp.session.get("/userinfo")
        if not resp.ok:
            flash(_("Failed to fetch user info from Authentik."),
                  category="error")
            return False
        info = resp.json()
        authentik_user_id = str(info.get("sub") or info.get("id") or "")
        if not authentik_user_id:
            flash(_("Authentik did not return a user id."), category="error")
            return False

        # Reuse calibre-web's existing bind-or-register logic
        from cps.oauth_bb import (oauth_update_token, bind_oauth_or_register,
                                  oauth_check)
        provider_id = str(oauth_prov.id)
        if provider_id not in oauth_check:
            oauth_check[provider_id] = "authentik"
        oauth_update_token(provider_id, token, authentik_user_id)
        return bind_oauth_or_register(provider_id, authentik_user_id,
                                      "authentik.login_authentik", "Authentik")

    log.info("Authentik OAuth blueprint registered")


# The login route is registered on the blueprint via redirect_to above.
# Flask-dance's OAuth2ConsumerBlueprint provides the ".login" endpoint
# automatically (it renders the authorization redirect).
# The "login_authentik" endpoint (referenced in redirect_to) must exist;
# we define it here as a simple landing that completes the OAuth handshake.
if _AUTHENTIK_BLUEPRINT is not None:
    @_AUTHENTIK_BLUEPRINT.route("/authentik", endpoint="login_authentik")
    @user_login_required
    def login_authentik():
        if not _AUTHENTIK_BLUEPRINT.session.authorized:
            return redirect(url_for("authentik.login"))
        try:
            resp = _AUTHENTIK_BLUEPRINT.session.get("/userinfo")
            if resp.ok:
                info = resp.json()
                authentik_user_id = str(
                    info.get("sub") or info.get("id") or "")
                from cps.oauth_bb import bind_oauth_or_register
                prov = ub.session.query(ub.OAuthProvider).filter_by(
                    provider_name="authentik").first()
                return bind_oauth_or_register(
                    str(prov.id), authentik_user_id,
                    "authentik.login", "Authentik")
            flash(_("Authentik OAuth error, please retry later."),
                  category="error")
        except (InvalidGrantError, TokenExpiredError) as e:
            flash(_("Authentik OAuth error: {}").format(e), category="error")
        return redirect(url_for("web.login"))
