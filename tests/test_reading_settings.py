"""Unit tests for the reading-settings page & proxy endpoints.

Covers:
  1. Settings page renders with data from moon-well (level select + save button).
  2. Settings page shows a retry-able error state when moon-well fails.
  3. GET /ajax/reading-settings proxies the upstream Result envelope as-is.
  4. POST /ajax/reading-settings/hard-level forwards {"hardLevel": N} upstream.
  5. Unauthenticated access is rejected.
"""
import json

import pytest


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


SETTINGS = {"hardLevel": 3, "hardLevelName": "CET4", "usingDefault": True,
            "options": [{"code": i, "name": "L%d" % i} for i in range(10)]}


def test_requires_login(app, moonwell_configured):
    """Anonymous requests must be redirected to the login page."""
    client = app.test_client()
    assert client.get("/reading/settings").status_code == 302
    assert client.get("/ajax/reading-settings").status_code == 302
    assert client.post("/ajax/reading-settings/hard-level",
                       json={"hardLevel": 3}).status_code == 302


def test_page_renders_with_settings(admin_client, moonwell_configured, monkeypatch):
    import cps.web as w

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST"):
        assert method == "GET" and path.endswith("/settings")
        return (json.dumps({"success": True, "result": SETTINGS}), 200,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(w, "_moonwell_proxy", fake_proxy)

    rv = admin_client.get("/reading/settings")
    assert rv.status_code == 200
    html = rv.data.decode("utf-8")
    assert "hard-level-select" in html
    assert "/ajax/reading-settings/hard-level" in html
    assert html.count("<option") == 10
    assert "selected" in html


def test_page_shows_error_when_upstream_fails(admin_client, moonwell_configured, monkeypatch):
    """moon-well 返回失败 → 页面渲染错误态而不是 500。"""
    import cps.web as w

    def failing_proxy(path, payload, timeout, label, binary=False, method="POST"):
        return (json.dumps({"success": False, "message": "boom"}), 503,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(w, "_moonwell_proxy", failing_proxy)

    rv = admin_client.get("/reading/settings")
    assert rv.status_code == 200
    html = rv.data.decode("utf-8")
    assert "alert-danger" in html
    assert "rs-retry" in html


def test_ajax_get_proxies_envelope(admin_client, moonwell_configured, monkeypatch):
    import cps.web as w

    captured = {}

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST"):
        captured["path"], captured["method"] = path, method
        return (json.dumps({"success": True, "result": SETTINGS}), 200,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(w, "_moonwell_proxy", fake_proxy)

    rv = admin_client.get("/ajax/reading-settings")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["success"] is True
    assert body["result"]["hardLevel"] == 3
    assert captured["method"] == "GET"
    assert captured["path"] == "/vocabulary/reading/settings"


def test_ajax_post_forwards_level(admin_client, moonwell_configured, monkeypatch):
    import cps.web as w

    captured = {}

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST"):
        captured["path"], captured["payload"] = path, payload
        return (json.dumps({"success": True,
                            "result": dict(SETTINGS, hardLevel=payload["hardLevel"],
                                           usingDefault=False)}), 200,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(w, "_moonwell_proxy", fake_proxy)

    rv = admin_client.post("/ajax/reading-settings/hard-level", json={"hardLevel": 8})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["result"]["hardLevel"] == 8
    assert captured["payload"] == {"hardLevel": 8}
    assert captured["path"] == "/vocabulary/reading/settings/hard-level"


def test_ajax_post_rejects_missing_level(admin_client, moonwell_configured):
    rv = admin_client.post("/ajax/reading-settings/hard-level", json={})
    assert rv.status_code == 400
    assert rv.get_json()["success"] is False
