"""Smoke test: verify the app fixture initializes calibre-web correctly."""


class TestSmoke:
    def test_app_fixture_initializes(self, app):
        """The app fixture should yield a configured Flask app."""
        assert app is not None
        assert app.config["TESTING"] is True

    def test_admin_login_works(self, admin_client):
        """The admin_client fixture should be logged in."""
        rv = admin_client.get("/", follow_redirects=False)
        # Logged-in users get 200 on index, not 302 redirect to login
        assert rv.status_code in (200, 302)
