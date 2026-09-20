"""Unit tests for the achievements page & claim CSRF handling.

Covers:
  1. Unauthenticated access is rejected.
  2. Achievements page renders with a page-local CSRF token input (#ach-csrf).
  3. POST /ajax/achievements-claim without X-CSRFToken is rejected with 400
     when CSRFProtect is enabled (regression: achievements.js used native
     fetch without the token, so claiming always 400'd).
  4. With the token from the rendered page, the same POST passes CSRF
     validation and the code is forwarded to the moon-well proxy.
"""
import json
import re

import pytest


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


@pytest.fixture
def csrf_enabled(app, monkeypatch):
    """conftest 全局关闭了 WTF_CSRF_ENABLED；这里临时打开以复现线上校验行为。"""
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    return app


def _page_csrf_token(admin_client):
    html = admin_client.get("/achievements").data.decode("utf-8")
    match = re.search(r'id="ach-csrf" value="([^"]+)"', html)
    assert match, "achievements page must render #ach-csrf token input"
    return match.group(1)


def test_requires_login(app, moonwell_configured):
    """Anonymous requests must be redirected to the login page."""
    client = app.test_client()
    assert client.get("/achievements").status_code == 302
    assert client.post("/ajax/achievements-claim", json={"code": "READ_1"}).status_code == 302


def test_page_renders_with_csrf_input(admin_client, moonwell_configured):
    rv = admin_client.get("/achievements")
    assert rv.status_code == 200
    html = rv.data.decode("utf-8")
    assert 'id="ach-csrf"' in html
    # 回归：script block 曾误写为 "scripts"（layout 槽位是 "js"），JS 从未加载
    assert "js/achievements.js" in html


def test_claim_without_csrf_token_rejected(admin_client, csrf_enabled,
                                           moonwell_configured):
    """无 token 的 claim POST 必须被 CSRFProtect 拦下（400），即修复前的线上行为。"""
    rv = admin_client.post("/ajax/achievements-claim", json={"code": "READ_1"},
                           headers={"X-Requested-With": "XMLHttpRequest"})
    assert rv.status_code == 400


def test_claim_with_csrf_token_proxies_code(admin_client, csrf_enabled,
                                            moonwell_configured, monkeypatch):
    """带上页面渲染的 token 后通过 CSRF 校验，code 原样转发 moon-well。"""
    import cps.web as w

    token = _page_csrf_token(admin_client)

    captured = {}

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST"):
        captured["path"] = path
        captured["payload"] = payload
        return (json.dumps({"success": True, "result": {"claimed": True}}), 200,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(w, "_moonwell_proxy", fake_proxy)

    rv = admin_client.post("/ajax/achievements-claim", json={"code": "READ_1"},
                           headers={"X-CSRFToken": token,
                                    "X-Requested-With": "XMLHttpRequest"})
    assert rv.status_code == 200
    assert rv.get_json() == {"success": True, "result": {"claimed": True}}
    assert captured["path"] == "/achievements/claim"
    assert captured["payload"] == {"code": "READ_1"}
