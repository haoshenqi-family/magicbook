"""R172 TED 原声伴听：两个薄代理 + 前端分流判据的守卫测试。

为什么必须分流（需求本质）：TED/博客类书的内容是**一段连续原声**
（`ted-audio/<slug>.aac`），文本段落只是这段录音上的时间轴切片；小说类书没有
原声，只能靠 `reading_tts` 逐段合成再拼接。若不分流，TED 点「整本朗读」= 用
机器音念文本（语义错）且白烧算力/积分。故：
  - 代理：`/ajax/ted-audio` → `/book/ted-audio`，`/ajax/ted-audio-paragraphs`
    → `/book/paragraph/list`（moon-well 零改动）。
  - 前端：运行时探测 `/ajax/ted-audio` 是否有整段原声（有 audioUrl 才走原声伴听，
    否则回落 R157 整本 TTS 连播）。**不得**用 `calibre.bookFormat === 'TED'`：那是
    Calibre 文件格式（epub/pdf），与 moon-well BookFormatEnum.TED 同名不同义，恒 false。

覆盖：
  1. 两个端点都要登录门禁。
  2. 转发路径 / body / Bearer / 内网绕过代理 / 超时。
  3. bookId 非数字 → 400，脏串绝不进上游 Long.valueOf。
  4. 上游错误按原状态码透传；上游不可达 → 503。
  5. 静态锁：分流由探测结果决定（且不得回退到 bookFormat）、按钮统一走 bookListenToggle、
     两端点在 read.html 注入。
"""

import json
import os
import re
import types

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


@pytest.fixture
def calibre_stub(monkeypatch):
    """桩掉 Calibre 库：book 143 = "Talk A" / "Speaker"。

    R200：代理改按书名+作者转发（moon-well 的 bookId 是它自己 book 表的 id，
    与 Calibre 书号是两套序列），故这里必须提供真实书对象。
    """
    # _ted_book_identity 定义在 cps.web，函数体读的是 cps.web 模块全局的 calibre_db
    # （reading.py 只 import 了函数名，本身没有 calibre_db 名字）。
    import cps.web as web_module

    book = types.SimpleNamespace(
        id=143, title="Talk A",
        authors=[types.SimpleNamespace(name="Speaker")])
    stub = types.SimpleNamespace(
        get_book=lambda bid: book if bid == 143 else None)
    monkeypatch.setattr(web_module, "calibre_db", stub)
    return book


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


def test_ted_audio_forwards_to_book_ted_audio(admin_client, calibre_stub, moonwell_configured,
                                              monkeypatch):
    captured = _capture_post(monkeypatch, _fake_response(
        200, {"success": True, "code": 200,
              "result": {"audioUrl": "http://minio/b/ted-audio/talk.aac"}}))

    rv = admin_client.post("/ajax/ted-audio", json={"bookId": " 143 "})
    assert rv.status_code == 200
    assert rv.get_json()["result"]["audioUrl"].endswith("talk.aac")

    assert captured["url"].endswith("/book/ted-audio")
    # R200 契约：按书名+作者查，绝不透传 Calibre 书号（两套 ID 序列只巧合对齐）
    assert captured["json"] == {"bookName": "Talk A", "author": "Speaker"}
    assert "bookId" not in captured["json"]
    assert captured["headers"].get("authorization") == "Bearer test-access-token"
    assert captured["proxies"] == {"http": None, "https": None}
    assert captured["timeout"] == 15


def test_ted_audio_paragraphs_forwards_to_paragraph_list(admin_client, calibre_stub,
                                                         moonwell_configured,
                                                         monkeypatch):
    captured = _capture_post(monkeypatch, _fake_response(
        200, {"success": True, "code": 200,
              "result": {"meta": {"slug": "talk"}, "paragraphs": []}}))

    rv = admin_client.post("/ajax/ted-audio-paragraphs", json={"bookId": "143"})
    assert rv.status_code == 200
    assert captured["url"].endswith("/book/paragraph/list")
    assert captured["json"] == {"bookName": "Talk A", "author": "Speaker"}
    assert captured["timeout"] == 15


@pytest.mark.parametrize("bad", ["abc", "143;DROP", "", None, 143.5])
def test_rejects_non_numeric_book_id(admin_client, calibre_stub, moonwell_configured,
                                     monkeypatch, bad):
    """bookId 直接进上游 Long.valueOf：脏串在代理层挡成 400，不透传成上游 500。"""
    import requests

    def boom(*args, **kwargs):
        raise AssertionError("upstream must not be called for a bad bookId")

    monkeypatch.setattr(requests, "post", boom)
    rv = admin_client.post("/ajax/ted-audio", json={"bookId": bad})
    assert rv.status_code == 400
    assert rv.get_json()["success"] is False


def test_passes_moonwell_error_through(admin_client, calibre_stub, moonwell_configured,
                                       monkeypatch):
    _capture_post(monkeypatch, _fake_response(
        500, {"code": 500, "msg": "ted audio unavailable"}))
    rv = admin_client.post("/ajax/ted-audio", json={"bookId": "143"})
    assert rv.status_code == 500
    assert "unavailable" in rv.get_json()["msg"]


def test_returns_503_when_upstream_unavailable(admin_client, calibre_stub, moonwell_configured,
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
    # R183（B4 批次 5）：#tts-book 绑定随沉浸式域迁至 reader-immersive.js，
    # 本文件的分流判据锁改读按 read.html 载入顺序拼接的 reader 模块全集
    from tests.reader_js_modules import reader_blob

    return reader_blob()


def test_shunt_is_runtime_probe_not_file_format():
    """分流判据必须是「运行时探测是否有整段原声」，而不是 calibre.bookFormat。

    Why: calibre.bookFormat 是 Calibre 文件格式（epub/pdf/txt，read.html 里来自 URL 的
    book_format 段），与 moon-well BookFormatEnum.TED 同名不同义；TED 书在 Calibre 里同样是
    epub ⇒ `=== 'TED'` 恒 false。R172 首版正因此从未生效（线上实测：代码已部署但 TED 仍播 TTS）。
    """
    src = _js()
    assert re.search(r"tedAudioMetaOk\s*=\s*!!tedAudioData\.audioUrl", src), \
        "探测结果未由 audioUrl 是否为空决定（有原声才分流）"
    assert re.search(r"TED_BOOK\s*=\s*tedAudioMetaOk", src), \
        "TED_BOOK 未由探测结果置位"
    assert not re.search(r"TED_BOOK\s*=\s*calibre\.bookFormat", src), \
        "分流判据不得再依赖 calibre.bookFormat（那是文件格式，恒不等于 'TED'）"


def test_tts_book_button_routed_through_probe():
    """#tts-book 必须统一走 bookListenToggle（探测完成后才决定原声伴听 / 整本 TTS）。"""
    src = _js()
    assert re.search(r"ttsBookBtn\.addEventListener\('click',\s*host\.bookListenToggle\)", src), \
        "#tts-book 未接 bookListenToggle（探测未完成时不得静态定分流）"
    assert re.search(r"function bookListenToggle\(\)", src), "缺少 bookListenToggle 定义"
    assert re.search(r"if \(data && data\.audioUrl\) \{ TED_BOOK = true", src), \
        "bookListenToggle 未按探测结果切到原声伴听"
    # R183（B4 批次 6）：bookPlayerToggle 归 I 节，TED 模块经宿主回调回落整本连播
    assert re.search(r"if \(calibre\.readingTtsUrl\) host\.bookPlayerToggle\(\)", src), \
        "无原声时未回落 R157 整本连播"
    assert not re.search(r"ttsBookBtn\.addEventListener\('click',\s*tedAudioToggle\)", src), \
        "不应再静态直连 tedAudioToggle（分流判据只能来自运行时探测）"


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


def test_unknown_calibre_book_returns_404_without_upstream(admin_client, calibre_stub,
                                                           moonwell_configured, monkeypatch):
    """书不存在时给确定 404，不把空书名送去上游当「未缓存」处理。"""
    import requests

    def boom(*args, **kwargs):
        raise AssertionError("upstream must not be called for a missing book")

    monkeypatch.setattr(requests, "post", boom)
    rv = admin_client.post("/ajax/ted-audio", json={"bookId": "999"})
    assert rv.status_code == 404
    assert rv.get_json()["success"] is False


def test_proxy_never_sends_calibre_book_id_as_moonwell_bookid():
    """负向锁：代理代码里不得再把 Calibre 书号当 moon-well bookId 透传。"""
    path = os.path.join(ROOT, "cps", "routes", "reading.py")
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    assert "\"bookId\": book_id" not in src and '"bookId": book_id' not in src, \
        "TED 代理不得再透传 Calibre 书号（R200）"
    assert "bookName" in src and "author" in src
