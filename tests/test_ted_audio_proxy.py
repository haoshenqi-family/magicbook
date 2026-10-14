"""R172 TED 原声伴听：两个薄代理 + 前端分流判据的守卫测试。

为什么必须分流（需求本质）：TED/博客类书的内容是**一段连续原声**
（`ted-audio/<slug>.aac`），文本段落只是这段录音上的时间轴切片；小说类书没有
原声，只能靠 `reading_tts` 逐段合成再拼接。若不分流，TED 点「整本朗读」= 用
机器音念文本（语义错）且白烧算力/积分。故：
  - 代理：`/ajax/ted-audio` → `/book/ted-audio`，`/ajax/ted-audio-paragraphs`
    → `/book/paragraph/list`（moon-well 零改动）。
  - 前端：`calibre.bookFormat === 'TED'` 分流到 tedAudioPlayer（静态锁）。

覆盖：
  1. 两个端点都要登录门禁。
  2. 转发路径 / body / Bearer / 内网绕过代理 / 超时。
  3. bookId 非数字 → 400，脏串绝不进上游 Long.valueOf。
  4. 上游错误按原状态码透传；上游不可达 → 503。
  5. 静态锁：分流判据存在、按钮接线接的是 tedAudioPlayer、两端点在 read.html 注入。
"""

import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPUB_JS = os.path.join(ROOT, "cps", "static", "js", "reading", "epub.js")
READ_HTML = os.path.join(ROOT, "cps", "templates", "read.html")


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


def _fake_response(status_code, body):
    class FakeResponse:
        pass
    resp = FakeResponse()
    resp.status_code = status_code
    resp.headers = {"Content-Type": "application/json"}
    resp.text = body if isinstance(body, str) else json.dumps(body)
    resp.content = resp.text.encode("utf-8")
    return resp


def _capture_post(monkeypatch, response):
    import requests
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        captured["proxies"] = proxies
        return response

    monkeypatch.setattr(requests, "post", fake_post)
    return captured


@pytest.mark.parametrize("path", ["/ajax/ted-audio", "/ajax/ted-audio-paragraphs"])
def test_requires_login(app, path):
    client = app.test_client()
    assert client.post(path, json={"bookId": "143"}).status_code == 302


def test_ted_audio_forwards_to_book_ted_audio(admin_client, moonwell_configured,
                                              monkeypatch):
    captured = _capture_post(monkeypatch, _fake_response(
        200, {"success": True, "code": 200,
              "result": {"audioUrl": "http://minio/b/ted-audio/talk.aac"}}))

    rv = admin_client.post("/ajax/ted-audio", json={"bookId": " 143 "})
    assert rv.status_code == 200
    assert rv.get_json()["result"]["audioUrl"].endswith("talk.aac")

    assert captured["url"].endswith("/book/ted-audio")
    assert captured["json"] == {"bookId": "143"}
    assert captured["headers"].get("authorization") == "Bearer test-access-token"
    assert captured["proxies"] == {"http": None, "https": None}
    assert captured["timeout"] == 15


def test_ted_audio_paragraphs_forwards_to_paragraph_list(admin_client,
                                                         moonwell_configured,
                                                         monkeypatch):
    captured = _capture_post(monkeypatch, _fake_response(
        200, {"success": True, "code": 200,
              "result": {"meta": {"slug": "talk"}, "paragraphs": []}}))

    rv = admin_client.post("/ajax/ted-audio-paragraphs", json={"bookId": "143"})
    assert rv.status_code == 200
    assert captured["url"].endswith("/book/paragraph/list")
    assert captured["json"] == {"bookId": "143"}
    assert captured["timeout"] == 15


@pytest.mark.parametrize("bad", ["abc", "143;DROP", "", None, 143.5])
def test_rejects_non_numeric_book_id(admin_client, moonwell_configured,
                                     monkeypatch, bad):
    """bookId 直接进上游 Long.valueOf：脏串在代理层挡成 400，不透传成上游 500。"""
    import requests

    def boom(*args, **kwargs):
        raise AssertionError("upstream must not be called for a bad bookId")

    monkeypatch.setattr(requests, "post", boom)
    rv = admin_client.post("/ajax/ted-audio", json={"bookId": bad})
    assert rv.status_code == 400
    assert rv.get_json()["success"] is False


def test_passes_moonwell_error_through(admin_client, moonwell_configured, monkeypatch):
    _capture_post(monkeypatch, _fake_response(
        500, {"code": 500, "msg": "ted audio unavailable"}))
    rv = admin_client.post("/ajax/ted-audio", json={"bookId": "143"})
    assert rv.status_code == 500
    assert "unavailable" in rv.get_json()["msg"]


def test_returns_503_when_upstream_unavailable(admin_client, moonwell_configured,
                                               monkeypatch):
    import requests

    def boom(*args, **kwargs):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(requests, "post", boom)
    rv = admin_client.post("/ajax/ted-audio-paragraphs", json={"bookId": "143"})
    assert rv.status_code == 503
    assert "service unavailable" in rv.get_json()["message"]


# ---------- 静态锁（防前端口径 / 接线漂移） ----------

def _js():
    with open(EPUB_JS, encoding="utf-8") as fh:
        return fh.read()


def test_book_format_ted_shunt_present():
    """分流判据必须是 calibre.bookFormat === 'TED'（与 moon-well BookFormatEnum.TED 对齐）。

    删掉该判据 → TED 会退回逐段 TTS（用机器音念文本），本断言须红（反向变异）。
    """
    assert re.search(r"TED_BOOK\s*=\s*calibre\.bookFormat\s*===\s*'TED'", _js()), \
        "epub.js 缺少 bookFormat === 'TED' 分流判据（须落在 TED_BOOK 赋值上，注释不算数）"


def test_tts_book_button_routed_to_ted_player():
    """同一个 #tts-book 按钮在 TED 书上必须接到 tedAudioToggle（否则分流形同虚设）。"""
    src = _js()
    assert re.search(r"ttsBookBtn\.addEventListener\('click',\s*tedAudioToggle\)",
                     src), "TED 分支未把 #tts-book 接到 tedAudioToggle"
    assert re.search(r"ttsBookBtn\.addEventListener\('click',\s*bookPlayerToggle\)",
                     src), "非 TED 分支应保留 R157 的 bookPlayerToggle"


def test_ted_player_uses_proxied_endpoints_and_highlights():
    """tedAudioPlayer 必须经 calibre 注入的两个代理取数，且用时间轴驱动高亮。"""
    src = _js()
    assert "calibre.tedAudioUrl" in src and "calibre.tedAudioParagraphsUrl" in src, \
        "tedAudioPlayer 未走注入的代理地址（防硬编码/指向漂移）"
    assert "reading-tts-speaking" in src, "缺少当前段高亮复用（.reading-tts-speaking）"
    assert "tedAudioSegmentAt" in src, "缺少时间轴命中当前段的实现"


def test_read_html_injects_ted_endpoints():
    with open(READ_HTML, encoding="utf-8") as fh:
        html = fh.read()
    assert "web.reading_ted_audio" in html, "read.html 未注入 /ajax/ted-audio 路由"
    assert "web.reading_ted_audio_paragraphs" in html, \
        "read.html 未注入 /ajax/ted-audio-paragraphs 路由"
