"""Unit tests for the reading TTS relay proxy (/ajax/reading-tts).

The reader's paragraph read-aloud is relayed through moon-well (which adapts
to Aliyun Bailian/DashScope), so magicbook's endpoint only proxies JSON in /
binary audio out over internal trust (OIDC identity headers, no token). Covers:
  1. Login required.
  2. Binary audio passthrough with identity headers (no authorization).
  3. Text validation (empty / over-length).
  4. moon-well JSON error (unconfigured Bailian) passthrough.
  5. Upstream network failure -> 503.
  6. CSRF protection when globally enabled.
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


def _post_tts(client, text="hello world"):
    return client.post("/ajax/reading-tts", json={"text": text})


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


def _audio_response():
    return _fake_response(200, {"Content-Type": "audio/mpeg"}, MP3)


def test_requires_login(app):
    """Anonymous requests must be redirected to the login page."""
    client = app.test_client()
    rv = _post_tts(client)
    assert rv.status_code == 302


def test_proxies_audio_passthrough(admin_client, moonwell_configured,
                                   monkeypatch):
    """Happy path: JSON in, mp3 bytes out, relayed over internal trust (no token)."""
    import requests

    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["proxies"] = proxies
        return _audio_response()

    monkeypatch.setattr(requests, "post", fake_post)

    rv = _post_tts(admin_client, text="A lucky serendipity happened.")
    assert rv.status_code == 200
    assert rv.mimetype == "audio/mpeg"
    assert rv.data == MP3

    assert captured["url"].endswith("/tts/speak")
    assert captured["json"] == {"text": "A lucky serendipity happened."}
    # 内网纯信任：不携带 authorization，改携 OIDC 身份头
    assert "authorization" not in captured["headers"]
    assert captured["headers"].get("X-User-Email")
    # moon-well 是内网服务：必须显式绕过环境代理
    assert captured["proxies"] == {"http": None, "https": None}


@pytest.mark.parametrize("text", ["", "   ", "x" * 2001])
def test_rejects_invalid_text(admin_client, moonwell_configured, text):
    """Empty or over-length text never reaches moon-well."""
    rv = _post_tts(admin_client, text=text)
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

    rv = _post_tts(admin_client)
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

    rv = _post_tts(admin_client)
    assert rv.status_code == 503
    body = rv.get_json()
    assert body["success"] is False
    assert "service unavailable" in body["message"]


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
