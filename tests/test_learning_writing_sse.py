"""写作批改 SSE 代理契约（R194）。

覆盖：
  1. 新端点要求登录。
  2. submit/revise 各自转到 moon-well 的 /stream 路径，payload 白名单化。
  3. 响应保持 text/event-stream，禁止缓冲头存在。
  4. 建连阶段 401 刷新一次后用新 Bearer 重连；流开始后不重放。
  5. 上游非 200 原样透传（JSON 错误），不伪装成空流。
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


def _sse_chunks():
    return [
        b'event:status\ndata:{"phase":"accepted"}\n\n',
        b'event:status\ndata:{"phase":"grading"}\n\n',
        b'event:ping\ndata:{"elapsedMs":5000}\n\n',
        b'event:result\ndata:{"success":true,"code":200,"result":{"draftNo":1,"overall":"ok"}}\n\n',
    ]


def _capture(monkeypatch, response):
    calls = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return response

    monkeypatch.setattr("cps.routes.learning.requests.post", fake_post)
    return calls


def test_stream_endpoints_require_login(app, moonwell_configured):
    client = app.test_client()
    for path in ("/ajax/learning/writing/submit/stream",
                 "/ajax/learning/writing/revise/stream"):
        assert client.post(path, json={"taskId": "7", "text": "x" * 200}).status_code == 302


def test_submit_stream_proxies_payload_and_headers(admin_client, moonwell_configured,
                                                     monkeypatch):
    calls = _capture(monkeypatch, FakeStreamResponse(chunks=_sse_chunks()))

    response = admin_client.post("/ajax/learning/writing/submit/stream",
                                 json={"taskId": "7", "text": "x" * 200,
                                       "ignored": "must not leak"})

    assert response.status_code == 200
    assert response.content_type.startswith("text/event-stream")
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.headers["X-Accel-Buffering"] == "no"

    assert len(calls) == 1
    call = calls[0]
    assert call["url"] == "https://moon-well.example.com/learning/writing/submit/stream"
    assert call["json"] == {"taskId": "7", "text": "x" * 200}
    assert call["stream"] is True
    assert call["timeout"] == (10, 300)
    assert call["headers"]["authorization"] == "Bearer test-access-token"
    assert call["headers"]["Accept"] == "text/event-stream"
    assert call["headers"]["X-Trace-Id"]

    body = response.get_data(as_text=True)
    for event in ("status", "ping", "result"):
        assert "event:" + event in body


def test_revise_stream_uses_revise_path(admin_client, moonwell_configured, monkeypatch):
    calls = _capture(monkeypatch, FakeStreamResponse(chunks=_sse_chunks()))

    response = admin_client.post("/ajax/learning/writing/revise/stream",
                                 json={"taskId": "7", "text": "x" * 200})

    assert response.status_code == 200
    assert calls[0]["url"] == "https://moon-well.example.com/learning/writing/revise/stream"


def test_stream_rejects_missing_required_fields_locally(admin_client, moonwell_configured,
                                                        monkeypatch):
    calls = _capture(monkeypatch, FakeStreamResponse(chunks=_sse_chunks()))

    for payload in ({}, {"taskId": "7"}, {"taskId": "7", "text": ""}):
        response = admin_client.post("/ajax/learning/writing/submit/stream", json=payload)
        assert response.status_code == 400
    assert not calls, "参数不合法时不该打到 moon-well"


def test_stream_401_refreshes_before_connecting_and_retries_once(admin_client,
                                                                 moonwell_configured,
                                                                 monkeypatch):
    first = FakeStreamResponse(status_code=401, text='{"success":false,"message":"expired"}',
                               headers={"Content-Type": "application/json"})
    second = FakeStreamResponse(chunks=_sse_chunks())
    calls = []
    responses = iter([first, second])

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return next(responses)

    monkeypatch.setattr("cps.routes.learning.requests.post", fake_post)
    monkeypatch.setattr(_mb_client, "refresh_session_token", lambda: "refreshed-token")

    response = admin_client.post("/ajax/learning/writing/submit/stream",
                                 json={"taskId": "7", "text": "x" * 200})

    assert response.status_code == 200
    assert len(calls) == 2
    assert calls[0]["headers"]["authorization"] == "Bearer test-access-token"
    assert calls[1]["headers"]["authorization"] == "Bearer refreshed-token"
    assert first.closed is True


def test_stream_passes_upstream_error_json_through(admin_client, moonwell_configured,
                                                   monkeypatch):
    upstream = FakeStreamResponse(
        status_code=500,
        text=json.dumps({"success": False, "code": 50515, "message": "正文太短"}),
        headers={"Content-Type": "application/json"},
    )
    _capture(monkeypatch, upstream)

    response = admin_client.post("/ajax/learning/writing/submit/stream",
                                 json={"taskId": "7", "text": "x" * 200})

    assert response.status_code == 500
    assert response.content_type.startswith("application/json")
    assert response.get_json()["code"] == 50515
    assert upstream.closed is True
