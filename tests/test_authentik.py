"""Tests for the Authentik OAuth integration."""
import json


class TestAuthentik:
    def test_register_authentik_no_config(self, app):
        """register_authentik should be a no-op when authentik is not configured."""
        from cps.ai.authentik import register_authentik
        # Should not raise even if no authentik provider row exists
        register_authentik(app)

    def test_register_authentik_with_config(self, app, ai_session):
        """When authentik config is present, the blueprint should register."""
        from cps.ai.models import AiProvider
        from cps.ai.crypto import encrypt_value
        from cps.ai.routes import _get_encryption_key

        # Add an authentik provider row with encrypted client_id and secret
        key = _get_encryption_key()
        prov = AiProvider()
        prov.provider_name = "authentik"
        prov.display_name = "Authentik"
        prov.api_base = "https://auth.example.com/application/o/calibre-web/"
        prov.api_key_encrypted = encrypt_value("test-client-id", key)
        prov.models_json = json.dumps(
            {"client_secret_encrypted": encrypt_value("test-secret", key)})
        prov.active = True
        ai_session.add(prov)
        ai_session.commit()

        from cps.ai.authentik import register_authentik, _AUTHENTIK_BLUEPRINT
        # The session-scoped app may have already handled a request (other
        # tests make HTTP calls), which blocks register_blueprint. Temporarily
        # lift the "first request" guard so we can test blueprint registration.
        had_first_request = app._got_first_request
        app._got_first_request = False
        try:
            register_authentik(app)
        finally:
            app._got_first_request = had_first_request

        # The login route should now exist
        rules = [r.rule for r in app.url_map.iter_rules()]
        assert any("/login/authentik" in r or "/login" in r for r in rules)
