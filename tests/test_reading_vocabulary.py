"""Unit tests for the reading-vocabulary proxy endpoint.

Covers:
  1. Unauthenticated access is rejected (login required).
  2. moon-well not configured -> 503 "not configured" (reader stays quiet).
  3. Configured + upstream success -> passthrough with userKey injected and
     X-Magicbook-Token header set.
  4. Configured + upstream failure -> 503 "service unavailable".
"""
import json

import pytest


@pytest.fixture
def moonwell_configured(monkeypatch):
    """Pretend the moon-well integration is configured."""
    from cps import constants

    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    monkeypatch.setattr(constants, "MOON_WELL_INTEGRATION_TOKEN",
                        "test-token")
    return constants


@pytest.fixture
def moonwell_unconfigured(monkeypatch):
    """Make sure the moon-well integration looks unconfigured."""
    from cps import constants

    monkeypatch.setattr(constants, "MOON_WELL_READING_URL", "")
    monkeypatch.setattr(constants, "MOON_WELL_INTEGRATION_TOKEN", "")
    return constants


def _post_vocab(client):
    """POST a sample word-context payload to the proxy endpoint."""
    return client.post("/ajax/reading-vocabulary", json={
        "bookId": 7,
        "bookName": "Sample Book",
        "chapter": "Chapter 1",
        "page": "3/120",
        "cfi": "epubcfi(/6/4!/4/2)",
        "words": [{"word": "serendipity", "sentence": "A lucky serendipity."}],
    })


def test_requires_login(app):
    """Anonymous requests must be redirected to the login page."""
    client = app.test_client()
    rv = _post_vocab(client)
    assert rv.status_code == 302


def test_returns_503_when_not_configured(admin_client, moonwell_unconfigured):
    """Without moon-well config the proxy answers 503 and stays quiet."""
    rv = _post_vocab(admin_client)
    assert rv.status_code == 503
    body = rv.get_json()
    assert body["success"] is False
    assert "not configured" in body["message"]


def test_proxies_successfully(admin_client, moonwell_configured, monkeypatch, ub_session):
    """Happy path: payload is forwarded with userKey + token, response passed back."""
    import requests

    from cps.ub import User

    admin_user = ub_session.query(User).filter_by(name="admin").first()

    captured = {}

    class FakeResponse:
        status_code = 200
        text = json.dumps({"result": [{"word": "serendipity",
                                       "translation": "好运", "unknown": True}]})
        headers = {"Content-Type": "application/json"}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    rv = _post_vocab(admin_client)
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["result"][0]["word"] == "serendipity"

    # 注入的是跨应用稳定标识 user_key（而非自增 user.id），供 moon-well 映射回 app_user
    assert admin_user.user_key
    assert captured["json"]["userKey"] == admin_user.user_key
    # 令牌只随 header 传递，绝不出现在请求体中
    assert captured["headers"]["X-Magicbook-Token"] == "test-token"
    assert "X-Magicbook-Token" not in captured["json"]
    # Token must not leak into the response either.
    assert "test-token" not in rv.get_data(as_text=True)
    assert captured["url"].endswith("/reading-vocabulary/analyze")


def test_returns_503_when_upstream_unavailable(admin_client, moonwell_configured,
                                               monkeypatch):
    """Network failure to moon-well surfaces as 503, not a crash."""
    import requests

    def fake_post(url, json=None, headers=None, timeout=None):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(requests, "post", fake_post)

    rv = _post_vocab(admin_client)
    assert rv.status_code == 503
    body = rv.get_json()
    assert body["success"] is False
    assert "service unavailable" in body["message"]
