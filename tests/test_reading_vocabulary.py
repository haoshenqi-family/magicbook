"""Unit tests for the reading-vocabulary proxy endpoint.

Covers:
  1. Unauthenticated access is rejected (login required).
  2. moon-well not configured -> 401 "not configured" (reader stays quiet).
  3. Configured but no moon-well JWT -> 401 "authorization required".
  4. Configured + upstream success -> passthrough with `authorization: Bearer`
     header set to the moon-well access token.
  5. Configured + upstream failure -> 503 "service unavailable".
  6. Session JWT rejected with 401 -> refresh token exchanged, request retried.
  7. Session JWT rejected and refresh fails -> 401 "login expired", tokens dropped.
  8. Client-supplied authorization header 401 -> passed through without refresh.
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


def _seed_moonwell_session(client, access_token="stale-access-token",
                           refresh_token="valid-refresh-token"):
    """Simulate tokens obtained at OIDC login time."""
    with client.session_transaction() as sess:
        sess["moonwell_access_token"] = access_token
        sess["moonwell_refresh_token"] = refresh_token


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

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["proxies"] = proxies
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
    assert captured["url"].endswith("/vocabulary/reading/analyze")
    # moon-well 是内网服务：必须显式绕过环境代理（http_proxy 会让内网请求 503）
    assert captured["proxies"] == {"http": None, "https": None}


def test_returns_503_when_upstream_unavailable(admin_client, moonwell_configured,
                                               monkeypatch):
    """Network failure to moon-well surfaces as 503, not a crash."""
    import requests

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(requests, "post", fake_post)

    rv = _post_vocab(admin_client, token="moonwell-jwt-abc")
    assert rv.status_code == 503
    body = rv.get_json()
    assert body["success"] is False
    assert "service unavailable" in body["message"]


def test_refreshes_session_token_on_401(admin_client, moonwell_configured,
                                        monkeypatch):
    """会话 access token 过期（401）时自动用 refresh token 换新并重试一次。

    moon-well access token 有效期 7 天且仅在 OIDC 登录时颁发，不刷新的话
    阅读词汇功能每 7 天就会静默 401，用户必须重新登录。
    """
    import requests

    calls = []

    class FakeUnauthorized:
        status_code = 401
        text = json.dumps({"code": 401, "message": "token invalid"})
        headers = {"Content-Type": "application/json"}

    class FakeRefreshResponse:
        status_code = 200
        text = json.dumps({"result": {"accessToken": "fresh-access-token",
                                      "refreshToken": "fresh-refresh-token"}})
        headers = {"Content-Type": "application/json"}

        def json(self):
            return json.loads(self.text)

    class FakeRefreshed:
        status_code = 200
        text = json.dumps({"result": [{"word": "serendipity", "unknown": True}]})
        headers = {"Content-Type": "application/json"}

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        calls.append({"url": url, "json": json, "headers": headers})
        if url.endswith("/auth/refreshToken"):
            return FakeRefreshResponse()
        if len(calls) == 1:
            return FakeUnauthorized()
        return FakeRefreshed()

    monkeypatch.setattr(requests, "post", fake_post)
    _seed_moonwell_session(admin_client)

    rv = _post_vocab(admin_client)
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["result"][0]["word"] == "serendipity"

    # 第一次用过期令牌，刷新后用新令牌重试
    assert calls[0]["headers"]["authorization"] == "Bearer stale-access-token"
    assert calls[0]["url"].endswith("/vocabulary/reading/analyze")
    assert calls[1]["url"].endswith("/auth/refreshToken")
    assert calls[1]["json"] == {"refreshToken": "valid-refresh-token"}
    assert calls[2]["headers"]["authorization"] == "Bearer fresh-access-token"

    # 会话中的令牌已更新，后续请求无需再刷新
    with admin_client.session_transaction() as sess:
        assert sess["moonwell_access_token"] == "fresh-access-token"
        assert sess["moonwell_refresh_token"] == "fresh-refresh-token"


def test_returns_401_when_refresh_fails(admin_client, moonwell_configured,
                                        monkeypatch):
    """refresh token 也失效时返回 401 提示重新登录，并清空会话令牌。"""
    import requests

    class FakeUnauthorized:
        status_code = 401
        text = json.dumps({"code": 401, "message": "token invalid"})
        headers = {"Content-Type": "application/json"}

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        return FakeUnauthorized()

    monkeypatch.setattr(requests, "post", fake_post)
    _seed_moonwell_session(admin_client)

    rv = _post_vocab(admin_client)
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
    """客户端自带 authorization 头时令牌生命周期由客户端自管，401 原样透传。"""
    import requests

    calls = []

    class FakeUnauthorized:
        status_code = 401
        text = json.dumps({"code": 401, "message": "token invalid"})
        headers = {"Content-Type": "application/json"}

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        calls.append(url)
        return FakeUnauthorized()

    monkeypatch.setattr(requests, "post", fake_post)
    _seed_moonwell_session(admin_client)

    rv = _post_vocab(admin_client, token="client-managed-token")
    assert rv.status_code == 401
    # 只有一次上游调用：没有触发 refresh（refresh 会调用 /auth/refreshToken）
    assert len(calls) == 1
    assert calls[0].endswith("/vocabulary/reading/analyze")


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


def test_translate_rejects_missing_csrf_when_protection_enabled(app, moonwell_configured):
    """划词翻译同样必须自带 X-CSRFToken：translateSelection 曾漏带头，
    生产环境 400（epub.js 已修复，本用例固化该接口的 CSRF 契约）。"""
    import re

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
        rv = client.post("/ajax/reading-translate",
                         json={"text": "serendipity", "context": "context"})
        assert rv.status_code == 400, "missing CSRF token must be rejected"

        # 带 X-CSRFToken → 通过 CSRF 校验
        rv = client.post("/ajax/reading-translate",
                         json={"text": "serendipity", "context": "context"},
                         headers={"X-CSRFToken": token})
        assert rv.status_code != 400, "request with CSRF token must pass CSRF"
    finally:
        app.config.update(WTF_CSRF_ENABLED=False)


def test_translate_batch_forwards_book_context(admin_client, moonwell_configured,
                                               monkeypatch):
    """整页翻译（前端逐段并发）：代理必须透传书名/章节（moon-well 提示词
    模板变量，供 LLM 保持全书译法一致），超长值截断到 200 字符。"""
    import requests

    captured = {}

    class FakeResponse:
        status_code = 200
        text = json.dumps({"result": ["译文"]})
        headers = {"Content-Type": "application/json"}

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    rv = admin_client.post("/ajax/reading-translate-batch", json={
        "paragraphs": ["One paragraph."],
        "bookName": "b" * 300,
        "chapter": "  Chapter 3  ",
    }, headers={"authorization": "Bearer moonwell-jwt-abc"})
    assert rv.status_code == 200

    payload = captured["json"]
    assert payload["paragraphs"] == ["One paragraph."]
    assert len(payload["bookName"]) == 200
    assert payload["chapter"] == "Chapter 3"


def test_csrf_time_limit_disabled_for_reading_pages(app):
    """阅读器页面长期保持打开时，模板渲染时嵌入的 CSRF token 不会随页刷新。

    flask-wtf 默认 WTF_CSRF_TIME_LIMIT=3600 会让超过 1 小时后的阅读请求
    （生词标注/划词翻译/沉浸式翻译/TTS/书签）全部 400。服务端已将其关闭
    （跟随签名会话 cookie 生效），本用例锁定该配置，防止回归。
    """
    assert app.config.get("WTF_CSRF_TIME_LIMIT") is None, \
        "WTF_CSRF_TIME_LIMIT must be None so long-open reader tokens don't expire"


def _reader_js_source(name):
    import os

    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "cps", "static", "js",
                        "libs" if name == "bar-ui.js" else "reading", name)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_epub_js_reloads_on_csrf_failure():
    """CSRF 失败自愈：token 过期/会话重建导致 reading 请求被 400 时，epub.js
    应刷新页面拿新 token（借助 localStorage 恢复阅读位置），而不是各功能
    静默失败。静态检查函数定义与其在翻译/TTS/沉浸式/生词标注/书签各条
    失败路径的引用。"""
    import re

    source = _reader_js_source("epub.js")
    assert 'function reloadIfCsrfBlocked' in source, \
        "epub.js must define reloadIfCsrfBlocked for CSRF-failure self-healing"
    assert "/csrf/i.test" in source, "CSRF detection must match response body text"
    # 定义 1 次 + 5 条 moon-well 相关失败路径（translate/tts/batch x2/vocabulary/bookmark）
    uses = len(re.findall(r"reloadIfCsrfBlocked\(", source))
    assert uses >= 6, f"expected reloadIfCsrfBlocked wired into all failure paths, got {uses}"
    # 每处 POST 都仍显式携带 CSRF 头（新功能接口易遗漏）
    assert source.count("X-CSRFToken") >= 6, \
        "all reader POSTs must carry X-CSRFToken"


def test_bar_ui_bookmark_requests_carry_csrf_token():
    """同类 CSRF 防线：音频阅读器 listenmp3.html 同样不加载 main.js（无全局
    $.ajaxSetup），bar-ui.js 里所有发往 set_bookmark 的 POST 必须携带
    csrf_token 表单字段，否则服务端全局 CSRF 会以 400 拦截，暂停/停止/
    结束时进度保存静默失效（曾遗漏 onpause/onstop/onfinish 三处）。"""
    import re

    source = _reader_js_source("bar-ui.js")
    total = len(re.findall(r"bookmark:\s*this\.position", source))
    with_token = len(re.findall(r"csrf_token.{0,80}?bookmark:\s*this\.position",
                                source, re.S))
    assert total == 4, f"expected 4 bookmark report points, got {total}"
    assert with_token == total, \
        f"{total - with_token} bookmark requests missing csrf_token (would 400)"