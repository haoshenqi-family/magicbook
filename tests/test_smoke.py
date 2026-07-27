"""Smoke test: verify the app fixture initializes calibre-web correctly."""


class TestSmoke:
    def test_app_fixture_initializes(self, app):
        """The app fixture should yield a configured Flask app."""
        assert app is not None
        assert app.config["TESTING"] is True

    def test_admin_login_works(self, admin_client):
        """The admin_client fixture should be logged in.

        We hit /ai/admin (which doesn't touch calibre_db) instead of /,
        because the index page queries calibre_db.session which is None
        in the test environment (no calibre metadata.db).
        """
        rv = admin_client.get("/ai/admin")
        # Admin page returns 200 for logged-in admins
        assert rv.status_code == 200
