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


# ################################### /ajax/reading-word-mark（划词气泡 ＋/－ 标记） ###

def _post_mark(client, word="serendipity", unknown=True, token=None):
    """POST a word-mark payload to the proxy endpoint."""
    headers = {"authorization": "Bearer " + token} if token else {}
    return client.post("/ajax/reading-word-mark",
                       json={"word": word, "unknown": unknown}, headers=headers)


class _FakeMoonwellGet:
    status_code = 200
    text = json.dumps({"success": True, "code": 200, "result": None})
    headers = {"Content-Type": "application/json"}


def test_word_mark_requires_login(app):
    """Anonymous marking requests must be redirected to the login page."""
    rv = _post_mark(app.test_client())
    assert rv.status_code == 302


def test_word_mark_returns_401_without_moonwell_jwt(admin_client, moonwell_configured):
    """No moon-well JWT in session/header -> authorization required."""
    rv = _post_mark(admin_client)
    assert rv.status_code == 401
    body = rv.get_json()
    assert body["success"] is False
    assert "authorization is required" in body["message"]


def test_word_mark_rejects_invalid_words(admin_client, moonwell_configured):
    """词会拼进 moon-well 的请求 path，非法输入必须 400 拒绝（防注入/防脏数据）。

    覆盖：空串、带空格短语、非 ASCII、path 遍历、query 注入、超长词、
    word=null（str(None) 会变成 "none" 存成脏词）、word 非 JSON 布尔
    （"false" 字符串经 bool() 恒为真，会误标为不认识）、首尾撇号/连字符
    （与页面分词 \\b 边界不匹配，标记后永远显示不出波浪线）。
    """
    bad_payloads = [
        {"word": "", "unknown": True},
        {"word": "hello world", "unknown": True},
        {"word": "你好", "unknown": True},
        {"word": "../admin", "unknown": True},
        {"word": "word?x=1", "unknown": True},
        {"word": "a" * 65, "unknown": True},
        {"word": "12abc", "unknown": True},
        {"word": None, "unknown": True},
        {"word": 123, "unknown": True},
        {"word": "serendipity", "unknown": "false"},
        {"word": "serendipity"},
        {"word": "apple'", "unknown": True},
        {"word": "apple-", "unknown": True},
        {"word": "'apple", "unknown": True},
    ]
    for payload in bad_payloads:
        rv = admin_client.post("/ajax/reading-word-mark", json=payload,
                               headers={"authorization": "Bearer moonwell-jwt-abc"})
        assert rv.status_code == 400, f"{payload!r} must be rejected with 400"
        body = rv.get_json()
        assert body["success"] is False


def test_word_mark_normalizes_word_and_proxies_unknown(admin_client,
                                                       moonwell_configured,
                                                       monkeypatch):
    """＋标记不认识：词形归一化（弯撇号→直撇号、小写）后转发 moon-well
    GET /vocabulary/unknown/{word}，与 ES 词 key / 前端 vocabularyRecords 一致。"""
    import requests

    captured = {}

    def fake_get(url, headers=None, timeout=None, proxies=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["proxies"] = proxies
        return _FakeMoonwellGet()

    monkeypatch.setattr(requests, "get", fake_get)

    rv = _post_mark(admin_client, word="Apple\u2019s", unknown=True,
                    token="moonwell-jwt-abc")
    assert rv.status_code == 200
    # 归一化：弯撇号 → 直撇号，大写 → 小写，再 URL 编码进 path
    assert captured["url"].endswith("/vocabulary/unknown/apple%27s")
    assert captured["headers"]["authorization"] == "Bearer moonwell-jwt-abc"
    # moon-well 是内网服务：必须显式绕过环境代理
    assert captured["proxies"] == {"http": None, "https": None}


def test_word_mark_proxies_known(admin_client, moonwell_configured, monkeypatch):
    """－标记已认识：转发 moon-well GET /vocabulary/known/{word}。"""
    import requests

    captured = {}

    def fake_get(url, headers=None, timeout=None, proxies=None):
        captured["url"] = url
        return _FakeMoonwellGet()

    monkeypatch.setattr(requests, "get", fake_get)

    rv = _post_mark(admin_client, word="serendipity", unknown=False,
                    token="moonwell-jwt-abc")
    assert rv.status_code == 200
    assert captured["url"].endswith("/vocabulary/known/serendipity")


def test_word_mark_returns_503_when_upstream_unavailable(admin_client,
                                                         moonwell_configured,
                                                         monkeypatch):
    """Network failure to moon-well surfaces as 503, not a crash."""
    import requests

    def fake_get(url, headers=None, timeout=None, proxies=None):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(requests, "get", fake_get)

    rv = _post_mark(admin_client, token="moonwell-jwt-abc")
    assert rv.status_code == 503
    body = rv.get_json()
    assert body["success"] is False
    assert "service unavailable" in body["message"]


def test_word_mark_refreshes_session_token_on_401(admin_client, moonwell_configured,
                                                  monkeypatch):
    """GET 转发同样支持会话令牌 401 自动刷新重试（_moonwell_proxy 的 GET 分支）。"""
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

    def fake_get(url, headers=None, timeout=None, proxies=None):
        calls.append({"url": url, "headers": headers})
        if len(calls) == 1:
            return FakeUnauthorized()
        return _FakeMoonwellGet()

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        calls.append({"url": url, "json": json})
        return FakeRefreshResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", fake_post)
    _seed_moonwell_session(admin_client)

    rv = _post_mark(admin_client)
    assert rv.status_code == 200

    # 第一次用过期令牌 GET，刷新后用新令牌重试 GET
    assert calls[0]["url"].endswith("/vocabulary/unknown/serendipity")
    assert calls[0]["headers"]["authorization"] == "Bearer stale-access-token"
    assert calls[1]["url"].endswith("/auth/refreshToken")
    assert calls[2]["headers"]["authorization"] == "Bearer fresh-access-token"


def test_word_mark_request_carries_csrf_token_contract(app, moonwell_configured):
    """划词标记同样必须自带 X-CSRFToken：EPUB 阅读器不加载 main.js，生产
    环境 CSRF 全局启用，缺 token 会被 400 拦截导致标记按钮静默失效。"""
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
        rv = client.post("/ajax/reading-word-mark",
                         json={"word": "serendipity", "unknown": True})
        assert rv.status_code == 400, "missing CSRF token must be rejected"

        # 带 X-CSRFToken → 通过 CSRF 校验
        rv = client.post("/ajax/reading-word-mark",
                         json={"word": "serendipity", "unknown": True},
                         headers={"X-CSRFToken": token})
        assert rv.status_code != 400, "request with CSRF token must pass CSRF"
    finally:
        app.config.update(WTF_CSRF_ENABLED=False)


def test_epub_js_popover_auto_close_and_mark_buttons():
    """划词气泡自动消失根因修复的静态锁定：

    1. iframe 内的 mousedown/keydown 不冒泡到主文档，必须绑定在 iframe
       document 上（bindSelectionTranslation 内），否则点击正文气泡常驻；
    2. translateSelection 的所有「不弹气泡」路径必须关闭旧气泡；
    3. 翻页（relocated）时旧气泡坐标失效，必须关闭；
    4. ＋/－ 标记按钮存在且单词词形才显示。
    """
    import re

    source = _reader_js_source("epub.js")

    # bindSelectionTranslation 内绑定了 iframe 的 mousedown 与 keydown
    assert re.search(
        r"bindSelectionTranslation\s*\(content\)\s*\{[\s\S]*?"
        r"content\.document\.addEventListener\('mousedown'[\s\S]*?"
        r"content\.document\.addEventListener\('keydown'",
        source), "iframe document must handle mousedown+keydown to close popover"
    # 不弹气泡路径都关闭旧气泡
    assert source.count("closeTranslationPopover(); return;") >= 2
    # 翻页关闭气泡
    assert re.search(r"'relocated', function \(\) \{\s*// 翻页后旧气泡"
                     r"[\s\S]*?closeTranslationPopover\(\);", source)
    # 标记按钮
    assert "appendWordMarkButtons" in source
    assert "readingWordMarkUrl" in source
    assert "SINGLE_WORD_RE" in source
    # 标记请求携带 CSRF 头（EPUB 阅读器无全局 $.ajaxSetup）
    assert re.search(r"readingWordMarkUrl[\s\S]{0,200}X-CSRFToken", source)
    # 供 ai_chat.js ESC 分层关闭的桥接对象
    assert "window.ReaderTranslation" in source
    # ESC 逐层退出：关闭气泡时必须阻断后注册的 ESC 监听（ai_chat.js 的
    # jQuery 委托监听在本 handler 之后注册），否则同开场景一次 ESC 连关
    # 气泡与抽屉两个面板（分层设计失效）
    assert re.search(r"if \(!translationPopover\) return;\s*"
                     r"closeTranslationPopover\(\);\s*"
                     r"event\.stopImmediatePropagation\(\);", source), \
        "ESC handler must stopImmediatePropagation after closing the popover"


def test_ai_chat_js_escape_closes_drawer():
    """ESC 关闭 AI 抽屉的静态锁定：气泡优先（ReaderTranslation.isOpen）
    时跳过，避免一次 ESC 连关气泡与抽屉两个面板。"""
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "cps", "static", "js", "ai_chat.js")
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    assert 'e.key !== "Escape"' in source
    assert "ReaderTranslation" in source and "isOpen()" in source
    assert 'closeDrawer()' in source

# ---------------------------------------------------------------------------
# Paragraph annotations (reading-annotation-* proxies)
# ---------------------------------------------------------------------------

def _post_annotation_create(client, paragraph="The moon is a friendless place.",
                            content="这段写得很孤独", book_name="Sample Book",
                            chapter="Chapter 3", token="moonwell-jwt-abc"):
    headers = {"authorization": "Bearer " + token} if token else {}
    return client.post("/ajax/reading-annotation-create", json={
        "paragraph": paragraph, "content": content,
        "bookName": book_name, "chapter": chapter,
    }, headers=headers)


def _post_annotation_list_by_paragraph(client,
                                       paragraph="The moon is a friendless place.",
                                       token="moonwell-jwt-abc"):
    headers = {"authorization": "Bearer " + token} if token else {}
    return client.post("/ajax/reading-annotation-list-by-paragraph",
                       json={"paragraph": paragraph}, headers=headers)


def _post_annotation_list_by_book(client, book_name="Sample Book",
                                  chapter=None, token="moonwell-jwt-abc"):
    headers = {"authorization": "Bearer " + token} if token else {}
    return client.post("/ajax/reading-annotation-list-by-book", json={
        "bookName": book_name, "chapter": chapter,
    }, headers=headers)


def test_annotation_create_requires_login(app):
    """Anonymous requests must be redirected to the login page."""
    client = app.test_client()
    rv = client.post("/ajax/reading-annotation-create",
                     json={"paragraph": "p", "content": "c"})
    assert rv.status_code == 302


def test_annotation_create_validates_payload(admin_client, moonwell_configured):
    """空段落/空内容/超长 → 400 即时拒绝，不打到 moon-well（批注是用户数据，
    校验失败必须明确告知而非静默）。"""
    rv = _post_annotation_create(admin_client, paragraph="   ", content="批注")
    assert rv.status_code == 400
    rv = _post_annotation_create(admin_client, paragraph="p", content="   ")
    assert rv.status_code == 400
    rv = _post_annotation_create(admin_client, paragraph="x" * 2001, content="批注")
    assert rv.status_code == 400
    rv = _post_annotation_create(admin_client, paragraph="p", content="批" * 2001)
    assert rv.status_code == 400
    # JSON null 不能被代理转换为字符串 "None" 后误接受
    rv = _post_annotation_create(admin_client, paragraph=None, content="批注")
    assert rv.status_code == 400
    rv = _post_annotation_create(admin_client, paragraph="p", content=None)
    assert rv.status_code == 400


def test_annotation_create_proxies_to_moonwell(admin_client, moonwell_configured,
                                               monkeypatch):
    """创建批注：转发 /reading/annotation/create；段落/内容 trim（与翻译/朗读
    链路同归一化，命中同一段落 ES 文档），书名/章节截断 200；署名与批注时间
    由 moon-well 从 JWT 用户取，代理不注入身份字段。"""
    import requests

    captured = {}

    class FakeResponse:
        status_code = 200
        text = json.dumps({"result": {"nickName": "书虫", "content": "批注",
                                      "annotatedAt": "2026-09-02T21:30:00"}})
        headers = {"Content-Type": "application/json"}

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["proxies"] = proxies
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    rv = _post_annotation_create(admin_client,
                                 paragraph="  The moon is a friendless place.  ",
                                 content="  这段写得很孤独  ",
                                 book_name="b" * 300, chapter="  Chapter 3  ")
    assert rv.status_code == 200

    assert captured["url"].endswith("/reading/annotation/create")
    payload = captured["json"]
    assert payload["paragraph"] == "The moon is a friendless place."
    assert payload["content"] == "这段写得很孤独"
    assert len(payload["bookName"]) == 200
    assert payload["chapter"] == "Chapter 3"
    assert captured["headers"]["authorization"] == "Bearer moonwell-jwt-abc"
    # 内网服务绕过环境代理（与其他阅读代理一致）
    assert captured["proxies"] == {"http": None, "https": None}


def test_annotation_create_503_when_upstream_unavailable(admin_client,
                                                         moonwell_configured,
                                                         monkeypatch):
    """Network failure to moon-well surfaces as 503, not a crash."""
    import requests

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(requests, "post", fake_post)

    rv = _post_annotation_create(admin_client)
    assert rv.status_code == 503
    body = rv.get_json()
    assert body["success"] is False
    assert "service unavailable" in body["message"]


def test_annotation_list_by_paragraph_validates_and_proxies(
        admin_client, moonwell_configured, monkeypatch):
    """按段查批注：空段落 400；正常转发 /reading/annotation/list-by-paragraph。"""
    import requests

    rv = _post_annotation_list_by_paragraph(admin_client, paragraph="   ")
    assert rv.status_code == 400
    rv = _post_annotation_list_by_paragraph(admin_client, paragraph=None)
    assert rv.status_code == 400

    captured = {}

    class FakeResponse:
        status_code = 200
        text = json.dumps({"result": [{"nickName": "书虫", "content": "批注",
                                       "annotatedAt": "2026-09-02T21:30:00"}]})
        headers = {"Content-Type": "application/json"}

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    rv = _post_annotation_list_by_paragraph(
        admin_client, paragraph="  The moon is a friendless place.  ")
    assert rv.status_code == 200
    assert captured["url"].endswith("/reading/annotation/list-by-paragraph")
    assert captured["json"]["paragraph"] == "The moon is a friendless place."


def test_annotation_list_by_book_validates_and_proxies(admin_client,
                                                       moonwell_configured,
                                                       monkeypatch):
    """按书查批注：书名必填 1..200；chapter 可选、缺省转发空串（moon-well
    侧空串即不按章节过滤）。"""
    import requests

    rv = _post_annotation_list_by_book(admin_client, book_name="   ")
    assert rv.status_code == 400

    captured = {}

    class FakeResponse:
        status_code = 200
        text = json.dumps({"result": [{"paragraph": "p", "chapter": "Chapter 3",
                                       "annotations": []}]})
        headers = {"Content-Type": "application/json"}

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    rv = _post_annotation_list_by_book(admin_client, chapter=None)
    assert rv.status_code == 200
    assert captured["url"].endswith("/reading/annotation/list-by-book")
    assert captured["json"]["bookName"] == "Sample Book"
    assert captured["json"]["chapter"] == ""

    rv = _post_annotation_list_by_book(admin_client, chapter="  Chapter 3  ")
    assert rv.status_code == 200
    assert captured["json"]["chapter"] == "Chapter 3"


def test_annotation_requests_must_carry_csrf_token(app, moonwell_configured):
    """批注三个端点与阅读器其他 POST 一样必须携带 X-CSRFToken（阅读器不加载
    main.js，无全局 $.ajaxSetup）。"""
    app.config.update(WTF_CSRF_ENABLED=True)
    try:
        client = app.test_client()

        html = client.get("/login").get_data(as_text=True)
        import re as _re
        m = _re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        assert m, "login page should render a csrf token"
        token = m.group(1)

        rv = client.post("/login", data={"username": "admin",
                                         "password": "admin123",
                                         "csrf_token": token})
        assert rv.status_code == 302

        for url in ("/ajax/reading-annotation-create",
                    "/ajax/reading-annotation-list-by-paragraph",
                    "/ajax/reading-annotation-list-by-book"):
            rv = client.post(url, json={"paragraph": "p", "content": "c",
                                        "bookName": "b"})
            assert rv.status_code == 400, f"missing CSRF must reject {url}"

            rv = client.post(url, json={"paragraph": "p", "content": "c",
                                        "bookName": "b"},
                             headers={"X-CSRFToken": token})
            assert rv.status_code != 400, f"CSRF token must pass {url}"
    finally:
        app.config.update(WTF_CSRF_ENABLED=False)


def test_epub_js_annotation_wiring_contract():
    """段落批注前端接线的静态锁定：

    1. 批注段落文本必须用与翻译/朗读相同的 paragraphSpeechText 归一化
       （moon-well 按 SHA-256(段落) 落到同一份 ES 文档，归一化不一致
       批注会挂到另一个文档上）；
    2. 批注请求携带 X-CSRFToken（阅读器无全局 $.ajaxSetup）；
    3. ESC 分层退出覆盖书批注面板与段落批注弹层；
    4. 翻页（relocated）时批注弹层随划词气泡一起关闭（坐标失效）；
    5. iframe 内 mousedown 同样关闭批注弹层。
    """
    import re

    source = _reader_js_source("epub.js")

    # 段落归一化契约：弹层与创建均基于 paragraphSpeechText
    assert re.search(r"function openAnnotationPopover\(el, btn\) \{[\s\S]{0,200}"
                     r"paragraphSpeechText\(el\)", source), \
        "annotation must key on the same normalized paragraph text"
    # 批注请求带 CSRF 头
    assert re.search(r"readingAnnotationCreateUrl[\s\S]{0,200}X-CSRFToken", source)
    assert re.search(r"readingAnnotationListUrl[\s\S]{0,200}X-CSRFToken", source)
    assert re.search(r"readingAnnotationBookUrl[\s\S]{0,200}X-CSRFToken", source)
    # ESC 分层退出：面板 → 弹层 → 划词气泡，各层 stopImmediatePropagation
    assert re.search(r"if \(annotationPanel\) \{\s*closeAnnotationPanel\(\);"
                     r"[\s\S]{0,80}stopImmediatePropagation", source)
    assert re.search(r"if \(annotationPopover\) \{\s*closeAnnotationPopover\(\);"
                     r"[\s\S]{0,80}stopImmediatePropagation", source)
    # 翻页关闭批注弹层
    assert re.search(r"'relocated', function \(\) \{[\s\S]{0,200}"
                     r"closeAnnotationPopover\(\);", source)
    # iframe 内 mousedown 关闭批注弹层
    assert re.search(r"content\.document\.addEventListener\('mousedown',"
                     r"[\s\S]{0,120}closeAnnotationPopover\(\);", source)
    # 段落按钮注入
    assert "reading-annotation-btn" in source
    assert "✎" in source
