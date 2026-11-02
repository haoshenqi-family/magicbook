"""单词编故事代理契约（R200）。

覆盖：
  1. 页面与四个 AJAX 端点都要求登录。
  2. due 只透传 count（白名单），manual 把整段粘贴折成单元素 words。
  3. 本地 400：非法 source/count/cefr、空词表、超长词表、非数字 id。
  4. SSE 流不缓冲、事件原样透传、401 建连前刷新一次。
  5. history/detail 走 GET 平路径，上游 50524 原样透传。
"""
import json

import pytest
from cps.moonwell.client import client as _mb_client


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


def _envelope(result):
    return json.dumps({"success": True, "code": 200, "message": "", "result": result})


def _json_headers():
    return {"Content-Type": "application/json"}


class RecordingProxy:
    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    def __call__(self, path, payload, timeout, label, binary=False, method="POST",
                 system_identity=None, identity_headers=None, bearer_token=None):
        self.calls.append({"path": path, "payload": payload, "method": method,
                           "timeout": timeout})
        body, status = self.replies[path]
        return body, status, _json_headers()

    def call_for(self, path):
        return next(call for call in self.calls if call["path"] == path)


class FakeStreamResponse:
    def __init__(self, status_code=200, chunks=None, text="", headers=None):
        self.status_code = status_code
        self._chunks = chunks or []
        self.text = text
        self.headers = headers or {"Content-Type": "text/event-stream"}
        self.closed = False

    def iter_content(self, chunk_size=None):
        for chunk in self._chunks:
            yield chunk

    def close(self):
        self.closed = True


STORY = {
    "id": 9,
    "source": "due",
    "words": ["relent", "harbor"],
    "title": "The Harbor",
    "storyText": "The captain **relented** at dawn.",
    "cards": [{"word": "relent", "meaning": "让步",
               "storySentence": "The captain relented at dawn.",
               "uncached": False, "missing": False}],
    "cefrLevel": "B1",
    "createdAt": "2026-10-22T20:00:00",
}


def _sse_chunks():
    return [
        b'event:status\ndata:{"phase":"accepted"}\n\n',
        b'event:status\ndata:{"phase":"generating"}\n\n',
        b'event:ping\ndata:{"elapsedMs":5000}\n\n',
        b'event:result\ndata:{"success":true,"code":200,"result":{"id":9,"title":"The Harbor"}}\n\n',
    ]


def _capture(monkeypatch, response):
    calls = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return response

    monkeypatch.setattr("cps.routes.learning.requests.post", fake_post)
    return calls


# ---------- 1. 鉴权与页面 ----------

def test_story_page_and_ajax_require_login(app, moonwell_configured):
    client = app.test_client()
    assert client.get("/learning/story").status_code == 302
    assert client.post("/ajax/learning/story/generate", json={"source": "due"}).status_code == 302
    assert client.post("/ajax/learning/story/generate/stream",
                       json={"source": "due"}).status_code == 302
    assert client.get("/ajax/learning/story/history").status_code == 302
    assert client.get("/ajax/learning/story/detail?id=9").status_code == 302


def test_story_page_renders_controls_and_module(admin_client):
    html = admin_client.get("/learning/story").data.decode("utf-8")
    for element in ("sw-story-source", "sw-story-due-go", "sw-story-manual-go",
                    "sw-story-result", "sw-story-history-panel"):
        assert 'id="%s"' % element in html, "编故事页缺 %s" % element
    assert "js/learning-story.js" in html
    assert "storyGenerateStream" in html and "readingTts" in html


# ---------- 2. JSON 生成代理 ----------

def test_generate_due_proxies_whitelisted_payload(admin_client, moonwell_configured,
                                                  monkeypatch):
    proxy = RecordingProxy({"/learning/story/generate": (_envelope(STORY), 200)})
    monkeypatch.setattr(_mb_client, "proxy", proxy)

    response = admin_client.post("/ajax/learning/story/generate",
                                 json={"source": "due", "count": 6,
                                       "words": ["must not leak"], "junk": "x"})

    assert response.status_code == 200
    assert response.get_json()["result"]["title"] == "The Harbor"
    call = proxy.call_for("/learning/story/generate")
    assert call["payload"] == {"source": "due", "count": 6}
    assert call["timeout"] == 120
    assert call["method"] == "POST"


def test_generate_manual_keeps_pasted_text_as_one_entry(admin_client,
                                                         moonwell_configured,
                                                         monkeypatch):
    proxy = RecordingProxy({"/learning/story/generate": (_envelope(STORY), 200)})
    monkeypatch.setattr(_mb_client, "proxy", proxy)

    pasted = "relent, harbor\nsmile"
    admin_client.post("/ajax/learning/story/generate",
                      json={"source": "manual", "words": [pasted], "count": 99})

    assert proxy.call_for("/learning/story/generate")["payload"] == {
        "source": "manual", "words": [pasted]}, "manual 不应带 count，且整段粘贴原样进单元素 list"


@pytest.mark.parametrize("payload", [
    {"source": "other"},
    {"source": "due", "count": 0},
    {"source": "due", "count": 9},
    {"source": "due", "count": True},
    {"source": "due", "count": "6"},
    {"source": "due", "cefrLevel": "Z9"},
    {"source": "manual"},
    {"source": "manual", "words": []},
    {"source": "manual", "words": "relent"},
    {"source": "manual", "words": ["x" * 2001]},
], ids=["bad-source", "count-0", "count-9", "count-bool", "count-string",
        "bad-cefr", "manual-empty", "manual-list-empty", "manual-not-list",
        "manual-too-long"])
def test_generate_rejects_invalid_payload_locally(admin_client, moonwell_configured,
                                                  monkeypatch, payload):
    proxy = RecordingProxy({})
    monkeypatch.setattr(_mb_client, "proxy", proxy)

    response = admin_client.post("/ajax/learning/story/generate", json=payload)

    assert response.status_code == 400
    assert not proxy.calls, "参数不合法时不该打到 moon-well"


# ---------- 3. SSE 生成代理 ----------

def test_generate_stream_proxies_payload_and_events(admin_client, moonwell_configured,
                                                    monkeypatch):
    calls = _capture(monkeypatch, FakeStreamResponse(chunks=_sse_chunks()))

    response = admin_client.post(
        "/ajax/learning/story/generate/stream",
        json={"source": "manual", "words": ["relent, harbor"]})

    assert response.status_code == 200
    assert response.content_type.startswith("text/event-stream")
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.headers["X-Accel-Buffering"] == "no"
    assert len(calls) == 1
    call = calls[0]
    assert call["url"] == "https://moon-well.example.com/learning/story/generate/stream"
    assert call["json"] == {"source": "manual", "words": ["relent, harbor"]}
    assert call["stream"] is True
    assert call["timeout"] == (10, 300)
    assert call["headers"]["authorization"] == "Bearer test-access-token"
    assert call["headers"]["Accept"] == "text/event-stream"
    body = response.get_data(as_text=True)
    for event in ("status", "ping", "result"):
        assert "event:" + event in body


def test_generate_stream_rejects_invalid_payload_locally(admin_client,
                                                         moonwell_configured,
                                                         monkeypatch):
    calls = _capture(monkeypatch, FakeStreamResponse(chunks=_sse_chunks()))
    response = admin_client.post("/ajax/learning/story/generate/stream",
                                 json={"source": "due", "count": 10})
    assert response.status_code == 400
    assert not calls


def test_generate_stream_401_refreshes_before_connecting(admin_client,
                                                          moonwell_configured,
                                                          monkeypatch):
    first = FakeStreamResponse(status_code=401,
                               text='{"success":false,"message":"expired"}',
                               headers={"Content-Type": "application/json"})
    second = FakeStreamResponse(chunks=_sse_chunks())
    calls = []
    responses = iter([first, second])

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return next(responses)

    monkeypatch.setattr("cps.routes.learning.requests.post", fake_post)
    monkeypatch.setattr(_mb_client, "refresh_session_token", lambda: "refreshed-token")

    response = admin_client.post("/ajax/learning/story/generate/stream",
                                 json={"source": "due", "count": 6})

    assert response.status_code == 200
    assert len(calls) == 2
    assert calls[1]["headers"]["authorization"] == "Bearer refreshed-token"
    assert first.closed is True


# ---------- 4. 历史与详情 ----------

def test_history_and_detail_forward_get_paths(admin_client, moonwell_configured,
                                              monkeypatch):
    proxy = RecordingProxy({
        "/learning/story/history": (_envelope([STORY]), 200),
        "/learning/story/9": (_envelope(STORY), 200),
    })
    monkeypatch.setattr(_mb_client, "proxy", proxy)

    assert admin_client.get("/ajax/learning/story/history").get_json()["result"][0]["id"] == 9
    assert admin_client.get("/ajax/learning/story/detail?id=9").get_json()["result"]["id"] == 9

    history = proxy.call_for("/learning/story/history")
    assert history["method"] == "GET" and history["payload"] is None
    detail = proxy.call_for("/learning/story/9")
    assert detail["method"] == "GET" and detail["payload"] is None


@pytest.mark.parametrize("query", ["", "?id=", "?id=abc", "?id=9x", "?id=" + "9" * 65])
def test_detail_rejects_non_numeric_id(admin_client, moonwell_configured,
                                       monkeypatch, query):
    proxy = RecordingProxy({})
    monkeypatch.setattr(_mb_client, "proxy", proxy)

    response = admin_client.get("/ajax/learning/story/detail" + query)

    assert response.status_code == 400
    assert not proxy.calls


def test_detail_passes_upstream_50524_through(admin_client, moonwell_configured,
                                              monkeypatch):
    body = json.dumps({"success": False, "code": 50524, "message": "故事不存在"})
    proxy = RecordingProxy({"/learning/story/9": (body, 500)})
    monkeypatch.setattr(_mb_client, "proxy", proxy)

    response = admin_client.get("/ajax/learning/story/detail?id=9")

    assert response.status_code == 500
    assert response.get_json()["code"] == 50524
