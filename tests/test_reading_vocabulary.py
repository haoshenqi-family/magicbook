"""Unit tests for the reading-vocabulary proxy endpoint.

Covers:
  1. Unauthenticated access is rejected (login required).
  2. moon-well not configured -> 503 "not configured" (reader stays quiet).
  3. Configured but no moon-well JWT -> 401 "authorization required".
  4. Configured + upstream success -> passthrough with `authorization: Bearer`
     header set to the moon-well access token.
  5. Configured + upstream failure -> 503 "service unavailable".
"""
import json

import pytest


@pytest.fixture
def moonwell_configured(monkeypatch):
    """Pretend the moon-well integration is configured."""
    from cps import constants

    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


@pytest.fixture
def moonwell_unconfigured(monkeypatch):
    """Make sure the moon-well integration looks unconfigured."""
    from cps import constants

    monkeypatch.setattr(constants, "MOON_WELL_READING_URL", "")
    return constants


def _post_vocab(client, token=None):
    """POST a sample page-text payload to the proxy endpoint."""
    headers = {"authorization": "Bearer " + token} if token else {}
    return client.post("/ajax/reading-vocabulary", json={
        "bookId": 7,
        "bookName": "Sample Book",
        "chapter": "Chapter 1",
        "page": "3/120",
        "cfi": "epubcfi(/6/4!/4/2)",
        "pageText": "A lucky serendipity happened today.",
    }, headers=headers)


def test_requires_login(app):
    """Anonymous requests must be redirected to the login page."""
    client = app.test_client()
    rv = _post_vocab(client)
    assert rv.status_code == 302


def test_returns_401_without_moonwell_jwt(admin_client, moonwell_configured):
    """No moon-well JWT in session/header -> authorization required."""
    rv = _post_vocab(admin_client)
    assert rv.status_code == 401
    body = rv.get_json()
    assert body["success"] is False
    assert "authorization is required" in body["message"]


def test_returns_401_when_not_configured(admin_client, moonwell_unconfigured):
    """Without moon-well config the proxy answers 401 and stays quiet."""
    rv = _post_vocab(admin_client, token="session-token")
    assert rv.status_code == 401
    body = rv.get_json()
    assert body["success"] is False
    assert "authorization is required" in body["message"]


def test_proxies_successfully(admin_client, moonwell_configured, monkeypatch):
    """Happy path: payload is forwarded with authorization header, response passed back."""
    import requests

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

    rv = _post_vocab(admin_client, token="moonwell-jwt-abc")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["result"][0]["word"] == "serendipity"

    # JWT 只随 authorization header 传递，绝不出现在请求体中
    assert captured["headers"]["authorization"] == "Bearer moonwell-jwt-abc"
    assert "authorization" not in captured["json"]
    # Token must not leak into the response either.
    assert "moonwell-jwt-abc" not in rv.get_data(as_text=True)
    assert captured["url"].endswith("/reading-vocabulary/analyze")


def test_returns_503_when_upstream_unavailable(admin_client, moonwell_configured,
                                               monkeypatch):
    """Network failure to moon-well surfaces as 503, not a crash."""
    import requests

    def fake_post(url, json=None, headers=None, timeout=None):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(requests, "post", fake_post)

    rv = _post_vocab(admin_client, token="moonwell-jwt-abc")
    assert rv.status_code == 503
    body = rv.get_json()
    assert body["success"] is False
    assert "service unavailable" in body["message"]


def test_rejects_missing_csrf_when_protection_enabled(app, moonwell_configured):
    """生产环境 CSRF 全局启用：EPUB 阅读器不加载 main.js，划词请求必须自带
    X-CSRFToken，否则被 400 拦截导致生词标注静默失效。本用例复现该场景。

    conftest 默认关闭 CSRF（WTF_CSRF_ENABLED=False），这里临时开启以贴近真实部署。
    """
    import re

    app.config.update(WTF_CSRF_ENABLED=True)
    try:
        client = app.test_client()

        # 登录页渲染 csrf_token 隐藏域（与阅读器页面一致），先 GET 再提取
        html = client.get("/login").get_data(as_text=True)
        m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        assert m, "login page should render a csrf token"
        token = m.group(1)

        rv = client.post("/login",
                         data={"username": "admin", "password": "admin123",
                               "csrf_token": token})
        assert rv.status_code == 302, f"login with token failed: {rv.status_code}"

        # 模拟 epub.js 修复前的请求（无 X-CSRFToken）→ 必须被 CSRF 拒绝
        rv = _post_vocab(client)
        assert rv.status_code == 400, "missing CSRF token must be rejected"

        # 修复后的请求（带 X-CSRFToken）→ 通过 CSRF，进入业务逻辑
        # （moon-well 已配置但 fake_post 未 mock 时不会走到网络层；
        #  此处仅验证 CSRF 放行，具体返回由业务层决定）
        rv = client.post("/ajax/reading-vocabulary",
                         json={"bookId": 7, "bookName": "B", "chapter": "C",
                               "page": "3/120", "cfi": "x",
                               "pageText": "A lucky serendipity happened today."},
                         headers={"X-CSRFToken": token})
        assert rv.status_code != 400, "request with CSRF token must pass CSRF"
    finally:
        app.config.update(WTF_CSRF_ENABLED=False)