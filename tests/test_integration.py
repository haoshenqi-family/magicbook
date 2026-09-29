"""End-to-end integration tests for the agent backendization transition (R98).

旧「chat 全链路」E2E 随 agent 后端化退役（对话编排已整体迁到 moon-well，其
等价 E2E 在 moon-well 的 AgentChatServiceIntegrationTest）。本文件现在验证
magicbook 侧的切换边界，走真实 Flask app + 两个 blueprint 共存：

  1. 旧写路径（/ai/chat 等）经真实 app 也返回 410 且不落数据；
  2. /ai/agent/* 薄代理经真实 app 转发（stub 掉 _moonwell_proxy / requests.post）；
  3. SSE 分型事件经真实 app 完整透传；
  4. 迁移窗口内旧读端点（history/memory GET）与新代理同时可用。
"""
import json
from unittest.mock import patch

import pytest

from cps.ai.models import AiConversation, AiMessage, AiUserMemory


def _ensure_db_configured():
    """Re-set config.db_configured = True before each request.

    calibre-web's admin.before_app_request redirects ALL non-exempt endpoints
    to admin.db_configuration when db_configured is False. Some operations
    (login, config commits) trigger config_sql invalidation which resets
    db_configured to False (no real metadata.db in the test env), causing
    subsequent GETs to return 302 redirects instead of JSON.
    """
    try:
        from cps import config as cw_config
        cw_config.db_configured = True
    except Exception:
        pass


class TestRetiredChatPath:
    def test_old_chat_flow_is_retired_and_persists_nothing(self, admin_client, app, ai_session):
        """旧全链路（配置+聊天）整体 410：ai_companion.db 冻结待迁移。"""
        _ensure_db_configured()
        rv = admin_client.post("/ai/chat", json={
            "book_id": 7, "message": "What is this book about?",
            "book_title": "Machine Learning Basics",
        })
        assert rv.status_code == 410
        assert rv.get_json()["gone"] is True
        assert ai_session.query(AiConversation).count() == 0
        assert ai_session.query(AiMessage).count() == 0

        # 管理页与 provider 测试同样退役
        assert admin_client.get("/ai/admin").status_code == 410
        assert admin_client.post("/ai/test_provider", json={}).status_code == 410


class TestAgentProxyEndToEnd:
    def test_conversations_relayed_through_real_app(self, admin_client, app, monkeypatch):
        """GET /ai/agent/conversations 经真实 Flask 路由转发到 moon-well 形制。"""
        captured = {}

        def fake_proxy(path, payload, timeout, label, **kwargs):
            captured.update({"path": path, "payload": payload})
            return json.dumps({"success": True, "result": [
                {"id": 3, "title": "第一章问过 sidebars", "bookId": 89}]}), 200, {}

        monkeypatch.setattr("cps.web._moonwell_proxy", fake_proxy)
        _ensure_db_configured()
        rv = admin_client.get("/ai/agent/conversations?bookId=89")
        assert rv.status_code == 200
        assert captured["path"] == "/ai/agent/conversations"
        assert captured["payload"] == {"bookId": 89}
        assert rv.get_json()["result"][0]["title"] == "第一章问过 sidebars"

    def test_memory_roundtrip_relayed_through_real_app(self, admin_client, app, monkeypatch):
        """记忆面板三步（list → save → list）都经薄代理，body 原样透传。"""
        seen = []

        def fake_proxy(path, payload, timeout, label, **kwargs):
            seen.append(path)
            if path.endswith("/save"):
                return json.dumps({"success": True, "result": {"id": 9, "memory": payload["memory"]}}), 200, {}
            return json.dumps({"success": True, "result": [{"id": 9, "memory": "偏好简洁"}]}), 200, {}

        monkeypatch.setattr("cps.web._moonwell_proxy", fake_proxy)
        _ensure_db_configured()
        rv = admin_client.post("/ai/agent/memory/save", json={"memory": "偏好简洁", "bookId": 89})
        assert rv.status_code == 200
        rv = admin_client.get("/ai/agent/memory")
        assert rv.status_code == 200
        assert seen == ["/ai/agent/memory/save", "/ai/agent/memory/list"]

    def test_sse_chat_streams_typed_events_through_real_app(self, admin_client, app, monkeypatch):
        """SSE 分型事件（delta/tool_call/tool_result/final）经真实 app 完整透传。"""
        from cps.ai import proxy as ai_proxy

        def fake_helpers():
            return ({}, lambda: "http://moonwell.test",
                    lambda: {"X-User-Subject": "sub-1"}, lambda: None)

        class FakeUpstream:
            status_code = 200
            text = ""

            def iter_content(self, chunk_size=None):
                yield b'event: tool_call\ndata: {"step":1,"name":"lookup_word","argsSummary":"word=muggle","requireConfirm":false}\n\n'
                yield b'event: tool_result\ndata: {"step":1,"name":"lookup_word","ok":true,"resultSummary":"\\u9ebb\\u74dc","durationMs":120}\n\n'
                yield b'event: delta\ndata: {"text":"muggle \\u662f\\u9ebb\\u74dc"}\n\n'
                yield b'event: final\ndata: {"conversationId":3,"messageId":9,"status":"COMPLETED","usage":{"promptTokens":100,"completionTokens":20}}\n\n'

            def close(self):
                pass

        monkeypatch.setattr(ai_proxy, "_web_helpers", fake_helpers)
        monkeypatch.setattr(ai_proxy.requests, "post",
                            lambda url, **kw: FakeUpstream())
        _ensure_db_configured()
        rv = admin_client.post("/ai/agent/chat", json={"message": "hi", "bookId": 89})
        assert rv.status_code == 200
        assert rv.mimetype == "text/event-stream"
        body = rv.get_data(as_text=True)
        # 五类分型事件全部原样到达，前端芯片/收尾逻辑可解析
        assert "event: tool_call" in body and "requireConfirm" in body
        assert "event: tool_result" in body
        assert "event: delta" in body
        assert "event: final" in body and '"conversationId":3' in body


class TestMigrationWindowCoexistence:
    def test_readonly_old_history_served_while_new_chat_active(self, admin_client, app, ai_session):
        """迁移窗口：旧读端点（SQLite 数据源）与新代理同时可用，互不干扰。"""
        conv = AiConversation(user_id=1, book_id=7, title="legacy thread")
        ai_session.add(conv)
        ai_session.commit()
        ai_session.add(AiMessage(conversation_id=conv.id, role="user", content="legacy question"))
        ai_session.add(AiUserMemory(user_id=1, content="legacy memory", source_book_id=7))
        ai_session.commit()

        _ensure_db_configured()
        rv = admin_client.get("/ai/history/%d" % conv.id)
        assert rv.status_code == 200
        assert rv.get_json()["messages"][0]["content"] == "legacy question"

        rv = admin_client.get("/ai/memory")
        assert rv.status_code == 200
        assert "legacy memory" in rv.get_json()["memories"]

        # 新端点仍由 moon-well 承载（stub 验证路由指向前方而非本地 SQLite）
        def fake_proxy(path, payload, timeout, label, **kwargs):
            assert path == "/ai/agent/conversations"
            return json.dumps({"success": True, "result": []}), 200, {}

        with patch("cps.web._moonwell_proxy", fake_proxy):
            rv = admin_client.get("/ai/agent/conversations?bookId=7")
            assert rv.status_code == 200
