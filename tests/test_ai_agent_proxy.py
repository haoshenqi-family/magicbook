"""Tests for cps/ai/proxy.py（/ai/agent/* 薄代理，R98）。

覆盖设计 §4.2 的四个要点：
- SSE 流式转发（chunk 完整性、不缓冲）
- token 刷新前置（连接建立阶段 401 → 刷新 → 重连一次；流开始后不再重试）
- 上游错误 JSON 原样透传（状态码 + body）
- JSON 端点复用 _moonwell_proxy 的形制适配（GET → moon-well POST body）

外部依赖全部替换：_web_helpers 打桩（不经 cps.web）、requests.post 打桩（不经网络）。
"""
import json
from types import SimpleNamespace

import pytest

from cps.ai import proxy as ai_proxy


class FakeUpstream:
    """requests.post 的假响应：status_code + 可迭代 body。"""

    def __init__(self, status_code=200, chunks=(), text=""):
        self.status_code = status_code
        self._chunks = [c.encode("utf-8") if isinstance(c, str) else c for c in chunks]
        self.text = text
        self.closed = False

    def iter_content(self, chunk_size=None):
        for chunk in self._chunks:
            yield chunk

    def close(self):
        self.closed = True


@pytest.fixture
def helpers(monkeypatch):
    """打桩 _web_helpers：base url / trace id / 刷新函数全部可控（R145 去 identity_headers）。"""
    state = {"refreshed_token": None}

    def _web_helpers():
        def refresh():
            state["refreshed_token"] = "fresh-token"
            return state["refreshed_token"]

        return ({}, lambda: "http://moonwell.test", refresh,
                lambda: "trace-test-id")

    monkeypatch.setattr(ai_proxy, "_web_helpers", _web_helpers)
    return state


@pytest.fixture
def posts(monkeypatch):
    """记录并接管 cps.ai.proxy 命名空间里的 requests.post。"""
    calls = []

    def install(responses):
        def fake_post(url, json=None, headers=None, **kwargs):
            calls.append({"url": url, "json": json, "headers": headers})
            return responses.pop(0)
        monkeypatch.setattr(ai_proxy.requests, "post", fake_post)

    install([])
    return SimpleNamespace(calls=calls, install=install)


def test_chat_streams_sse_chunks_unbuffered(admin_client, helpers, posts):
    events = [b"event: delta\n", b'data: {"text":"\\u4f60"}\n\n',
              b"event: final\n", b'data: {"conversationId": 3}\n\n']
    posts.install([FakeUpstream(200, chunks=events)])

    rv = admin_client.post("/ai/agent/chat", json={"message": "hi", "bookId": 89})
    assert rv.status_code == 200
    assert rv.mimetype == "text/event-stream"
    # chunk 原样到达（不缓冲、不改写），event: 行保留
    assert b"event: delta" in rv.data and b'"text"' in rv.data
    assert b"event: final" in rv.data
    # 上游地址与 Bearer 凭证（conftest 注入的会话 token；R145 互信头已下线）
    assert posts.calls[0]["url"] == "http://moonwell.test/ai/agent/chat"
    assert posts.calls[0]["headers"]["authorization"] == "Bearer test-access-token"


def test_chat_upstream_401_refreshes_then_retries(admin_client, helpers, posts):
    posts.install([
        FakeUpstream(401, text="expired"),
        FakeUpstream(200, chunks=[b'event: delta\ndata: {"text":"ok"}\n\n']),
    ])
    # 会话里必须有旧 token，401 重试分支才会触发（生产常态：JWT 过期）
    with admin_client.session_transaction() as sess:
        sess["moonwell_access_token"] = "stale-token"
    rv = admin_client.post("/ai/agent/chat", json={"message": "hi"})
    assert rv.status_code == 200
    assert helpers["refreshed_token"] == "fresh-token"
    # 第一次 401 连接被关闭，重连一次且带上新 Bearer
    assert len(posts.calls) == 2
    assert posts.calls[1]["headers"]["authorization"] == "Bearer fresh-token"


def test_chat_upstream_error_relays_json(admin_client, helpers, posts):
    error_body = json.dumps({"success": False, "message": "AI agent 功能未开启"})
    posts.install([FakeUpstream(500, text=error_body)])

    rv = admin_client.post("/ai/agent/chat", json={"message": "hi"})
    assert rv.status_code == 500
    assert rv.get_json()["message"] == "AI agent 功能未开启"


def test_chat_relay_uses_raw_request_payload(admin_client, helpers, posts):
    """薄代理不改写业务字段：conversationId/bookContext 原样上抛。"""
    payload = {"conversationId": 5, "message": "hi", "bookId": 89,
               "bookContext": {"chapter": "ch1"}}
    posts.install([FakeUpstream(200, chunks=[])])
    rv = admin_client.post("/ai/agent/chat", json=payload)
    assert rv.status_code == 200
    sent = posts.calls[0]["json"]
    assert sent["bookContext"]["chapter"] == "ch1"
    assert sent["conversationId"] == 5


def test_json_endpoints_reuse_moonwell_proxy(admin_client, monkeypatch):
    """GET 形制适配：/ai/agent/conversations?bookId= → _moonwell_proxy POST {bookId}。"""
    captured = {}

    def fake_proxy(path, payload, timeout, label, **kwargs):
        captured["path"] = path
        captured["payload"] = payload
        return json.dumps({"success": True, "result": [{"id": 1}]}), 200, {
            "Content-Type": "application/json"}

    monkeypatch.setattr("cps.web._moonwell_proxy", fake_proxy)
    rv = admin_client.get("/ai/agent/conversations?bookId=89")
    assert rv.status_code == 200
    assert captured["path"] == "/ai/agent/conversations"
    assert captured["payload"] == {"bookId": 89}
    assert rv.get_json()["result"][0]["id"] == 1


def test_history_requires_conversation_id(admin_client):
    rv = admin_client.get("/ai/agent/history")
    assert rv.status_code == 400


def test_book_profile_requires_book_id(admin_client):
    rv = admin_client.get("/ai/agent/book-profile")
    assert rv.status_code == 400


def test_memory_save_relays_body(admin_client, monkeypatch):
    captured = {}

    def fake_proxy(path, payload, timeout, label, **kwargs):
        captured.update({"path": path, "payload": payload})
        return json.dumps({"success": True, "result": {"id": 9}}), 200, {}

    monkeypatch.setattr("cps.web._moonwell_proxy", fake_proxy)
    rv = admin_client.post("/ai/agent/memory/save",
                           json={"memory": "偏好简洁", "bookId": 89})
    assert rv.status_code == 200
    assert captured["path"] == "/ai/agent/memory/save"
    assert captured["payload"]["memory"] == "偏好简洁"
