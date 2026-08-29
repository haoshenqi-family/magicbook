"""Unit tests for the reading TTS relay proxy (/ajax/reading-tts).

The reader's paragraph read-aloud is relayed through moon-well (which adapts
to Aliyun Bailian/DashScope), so magicbook's endpoint only proxies JSON in /
binary audio out using the caller's moon-well JWT. Covers:
  1. Login required.
  2. moon-well JWT missing -> 401.
  3. Binary audio passthrough with the session JWT.
  4. Text validation (empty / over-length).
  5. moon-well JSON error (unconfigured Bailian) passthrough.
  6. Upstream network failure -> 503.
  7. Session token 401 -> refresh + retry once.
  8. Refresh failure -> 401, session tokens dropped.
  9. Client-managed token 401 passthrough without refresh.
 10. CSRF protection when globally enabled.
"""
import json
import re

import pytest

MP3 = bytes([0x49, 0x44, 0x33, 0x04, 0x00, 0x00, 0x00, 0x00])


@pytest.fixture
def moonwell_configured(monkeypatch):
    """Pretend the moon-well integration is configured."""
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


def _post_tts(client, text="hello world", token=None):
    headers = {"authorization": "Bearer " + token} if token else {}
    return client.post("/ajax/reading-tts", json={"text": text},
                       headers=headers)


def _seed_moonwell_session(client, access_token="stale-access-token",
                           refresh_token="valid-refresh-token"):
    """Simulate tokens obtained at OIDC login time."""
    with client.session_transaction() as sess:
        sess["moonwell_access_token"] = access_token
        sess["moonwell_refresh_token"] = refresh_token


def _fake_response(status_code, headers, body):
    """A requests-like fake exposing both text and content (binary relay)."""
    class FakeResponse:
        pass
    resp = FakeResponse()
    resp.status_code = status_code
    resp.headers = headers
    if isinstance(body, bytes):
        resp.content = body
        resp.text = body.decode("utf-8", "replace")
    else:
        resp.text = body
        resp.content = body.encode("utf-8")
    return resp


def _json_response(status_code, obj):
    """JSON fake with a working .json() (instance attr shadows the method)."""
    resp = _fake_response(status_code, {"Content-Type": "application/json"},
                          json.dumps(obj))
    resp.json = lambda: obj
    return resp


def _audio_response():
    return _fake_response(200, {"Content-Type": "audio/mpeg"}, MP3)


def test_requires_login(app):
    """Anonymous requests must be redirected to the login page."""
    client = app.test_client()
    rv = _post_tts(client)
    assert rv.status_code == 302


def test_returns_401_without_moonwell_jwt(admin_client, moonwell_configured):
    """No moon-well JWT in session/header -> authorization required."""
    rv = _post_tts(admin_client)
    assert rv.status_code == 401
    body = rv.get_json()
    assert body["success"] is False
    assert "authorization is required" in body["message"]


def test_proxies_audio_passthrough(admin_client, moonwell_configured,
                                    monkeypatch):
    """Happy path: JSON in, mp3 bytes out, relayed with the session JWT."""
    import requests

    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["proxies"] = proxies
        return _audio_response()

    monkeypatch.setattr(requests, "post", fake_post)
    _seed_moonwell_session(admin_client)

    rv = _post_tts(admin_client, text="A lucky serendipity happened.")
    assert rv.status_code == 200
    assert rv.mimetype == "audio/mpeg"
    assert rv.data == MP3

    assert captured["url"].endswith("/tts/speak")
    assert captured["json"] == {"text": "A lucky serendipity happened."}
    # JWT 只随 authorization header 传递，绝不出现在请求体中
    assert captured["headers"]["authorization"] == "Bearer stale-access-token"
    assert "authorization" not in captured["json"]
    # moon-well 是内网服务：必须显式绕过环境代理
    assert captured["proxies"] == {"http": None, "https": None}


@pytest.mark.parametrize("text", ["", "   ", "x" * 2001])
def test_rejects_invalid_text(admin_client, moonwell_configured, text):
    """Empty or over-length text never reaches moon-well."""
    rv = _post_tts(admin_client, text=text, token="moonwell-jwt-abc")
    assert rv.status_code == 400
    body = rv.get_json()
    assert body["success"] is False
    assert "text" in body["message"]


def test_passes_moonwell_json_error_through(admin_client,
                                             moonwell_configured,
                                             monkeypatch):
    """moon-well 返回 JSON 错误（如百炼未配置）时按原状态码和 body 透传，
    前端据 Content-Type 判别并降级到浏览器语音。"""
    import requests

    error = _fake_response(500, {"Content-Type": "application/json"},
                           json.dumps({"code": 500,
                                       "msg": "TTS 未配置：请设置 DASHSCOPE_API_KEY"}))

    monkeypatch.setattr(requests, "post", lambda *a, **kw: error)

    rv = _post_tts(admin_client, token="moonwell-jwt-abc")
    assert rv.status_code == 500
    assert rv.mimetype == "application/json"
    body = rv.get_json()
    assert "DASHSCOPE_API_KEY" in body["msg"]


def test_returns_503_when_upstream_unavailable(admin_client,
                                                moonwell_configured,
                                                monkeypatch):
    """Network failure to moon-well surfaces as 503 JSON, not a crash."""
    import requests

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(requests, "post", fake_post)

    rv = _post_tts(admin_client, token="moonwell-jwt-abc")
    assert rv.status_code == 503
    body = rv.get_json()
    assert body["success"] is False
    assert "service unavailable" in body["message"]


def test_refreshes_session_token_on_401(admin_client, moonwell_configured,
                                         monkeypatch):
    """会话 access token 过期（401）时自动用 refresh token 换新并重试一次。"""
    import requests

    calls = []

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        calls.append({"url": url, "json": json, "headers": headers})
        if url.endswith("/auth/refreshToken"):
            return _json_response(200, {"result": {
                "accessToken": "fresh-access-token",
                "refreshToken": "fresh-refresh-token"}})
        if len(calls) == 1:
            return _json_response(401, {"code": 401, "msg": "token invalid"})
        return _audio_response()

    monkeypatch.setattr(requests, "post", fake_post)
    _seed_moonwell_session(admin_client)

    rv = _post_tts(admin_client)
    assert rv.status_code == 200
    assert rv.data == MP3

    # 第一次用过期令牌，刷新后用新令牌重试
    assert calls[0]["headers"]["authorization"] == "Bearer stale-access-token"
    assert calls[0]["url"].endswith("/tts/speak")
    assert calls[1]["url"].endswith("/auth/refreshToken")
    assert calls[1]["json"] == {"refreshToken": "valid-refresh-token"}
    assert calls[2]["headers"]["authorization"] == "Bearer fresh-access-token"

    with admin_client.session_transaction() as sess:
        assert sess["moonwell_access_token"] == "fresh-access-token"
        assert sess["moonwell_refresh_token"] == "fresh-refresh-token"


def test_returns_401_when_refresh_fails(admin_client, moonwell_configured,
                                         monkeypatch):
    """refresh token 也失效时返回 401 提示重新登录，并清空会话令牌。"""
    import requests

    unauthorized = _fake_response(401, {"Content-Type": "application/json"},
                                  json.dumps({"code": 401, "msg": "token invalid"}))
    monkeypatch.setattr(requests, "post", lambda *a, **kw: unauthorized)
    _seed_moonwell_session(admin_client)

    rv = _post_tts(admin_client)
    assert rv.status_code == 401
    body = rv.get_json()
    assert body["success"] is False
    assert "sign in again" in body["message"]

    with admin_client.session_transaction() as sess:
        assert "moonwell_access_token" not in sess
        assert "moonwell_refresh_token" not in sess


def test_client_token_401_is_passed_through_without_refresh(admin_client,
                                                             moonwell_configured,
                                                             monkeypatch):
    """客户端自带 authorization 头时 401 原样透传，不触发刷新。"""
    import requests

    calls = []
    unauthorized = _fake_response(401, {"Content-Type": "application/json"},
                                  json.dumps({"code": 401, "msg": "token invalid"}))

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        calls.append(url)
        return unauthorized

    monkeypatch.setattr(requests, "post", fake_post)
    _seed_moonwell_session(admin_client)

    rv = _post_tts(admin_client, token="client-managed-token")
    assert rv.status_code == 401
    # 只有一次上游调用：没有触发 refresh（refresh 会调用 /auth/refreshToken）
    assert len(calls) == 1
    assert calls[0].endswith("/tts/speak")


def test_rejects_missing_csrf_when_protection_enabled(app, moonwell_configured):
    """生产环境 CSRF 全局启用：阅读器 fetch 请求必须自带 X-CSRFToken。"""
    app.config.update(WTF_CSRF_ENABLED=True)
    try:
        client = app.test_client()

        html = client.get("/login").get_data(as_text=True)
        m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        assert m, "login page should render a csrf token"
        token = m.group(1)

        rv = client.post("/login",
                         data={"username": "admin", "password": "admin123",
                               "csrf_token": token})
        assert rv.status_code == 302, f"login with token failed: {rv.status_code}"

        # 无 X-CSRFToken → 必须被 CSRF 拒绝
        rv = client.post("/ajax/reading-tts", json={"text": "hello"})
        assert rv.status_code == 400, "missing CSRF token must be rejected"

        # 带 X-CSRFToken → 通过 CSRF 校验
        rv = client.post("/ajax/reading-tts", json={"text": "hello"},
                         headers={"X-CSRFToken": token})
        assert rv.status_code != 400, "request with CSRF token must pass CSRF"
    finally:
        app.config.update(WTF_CSRF_ENABLED=False)
