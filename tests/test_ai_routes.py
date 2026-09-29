"""Tests for the legacy AI companion endpoints after the agent backendization
switch (R98): chat/管理写路径永久 410 停写，读路径保留到迁移验证完成。

覆盖设计 magicbook 侧 §6.2 的切换语义：
- 写端点（chat/conversations POST/rename/history DELETE/memory clear/
  test_provider/admin）→ 410 + gone 标记，且绝不再写 ai_companion.db；
- 读端点（conversations/history/memory GET）维持原行为（旧会话只读可见）。
"""
import pytest

from cps.ai.models import (AiConfig, AiConversation, AiMessage, AiProvider,
                           AiUserMemory)


def _gone(rv):
    assert rv.status_code == 410
    data = rv.get_json()
    assert data["gone"] is True


class TestRetiredWriteEndpoints:
    """写路径全部 410：ai_companion.db 冻结，等迁移脚本一次性搬走。"""

    def test_chat_is_gone(self, admin_client, ai_session):
        _gone(admin_client.post("/ai/chat", json={"book_id": 1, "message": "hi"}))

    def test_new_conversation_is_gone(self, admin_client, ai_session):
        _gone(admin_client.post("/ai/conversations/7", json={}))

    def test_rename_is_gone(self, admin_client, ai_session):
        _gone(admin_client.post("/ai/conversations/1/rename", json={"title": "t"}))

    def test_clear_history_is_gone(self, admin_client, ai_session):
        _gone(admin_client.delete("/ai/history/1"))

    def test_clear_memory_is_gone(self, admin_client, ai_session):
        _gone(admin_client.post("/ai/memory/clear"))

    def test_test_provider_is_gone(self, admin_client, ai_session):
        _gone(admin_client.post("/ai/test_provider", json={"api_base": "https://x", "model": "m"}))

    def test_admin_page_is_gone(self, admin_client):
        _gone(admin_client.get("/ai/admin"))
        _gone(admin_client.post("/ai/admin", data={}))

    def test_chat_does_not_persist_anything(self, admin_client, ai_session):
        """410 之外的关键断言：停写——SQLite 里不会出现新会话/新消息。"""
        before_convs = ai_session.query(AiConversation).count()
        before_msgs = ai_session.query(AiMessage).count()
        admin_client.post("/ai/chat", json={"book_id": 1, "message": "hi"})
        assert ai_session.query(AiConversation).count() == before_convs
        assert ai_session.query(AiMessage).count() == before_msgs


class TestReadOnlyRemnants:
    """读端点保留原行为：迁移验证期内旧会话仍可查（只读）。"""

    def test_history_empty_for_unknown_conversation(self, admin_client):
        rv = admin_client.get("/ai/history/999999")
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["messages"] == []
        assert data["conversation"] is None

    def test_conversations_list(self, admin_client, ai_session):
        c1 = AiConversation(user_id=1, book_id=7, title="thread A")
        c2 = AiConversation(user_id=1, book_id=7, title="thread B")
        c3 = AiConversation(user_id=1, book_id=8, title="other book")
        c4 = AiConversation(user_id=2, book_id=7, title="other user")
        ai_session.add_all([c1, c2, c3, c4])
        ai_session.commit()

        rv = admin_client.get("/ai/conversations/7")
        assert rv.status_code == 200
        convs = rv.get_json()["conversations"]
        ids = {c["id"] for c in convs}
        assert ids == {c1.id, c2.id}
        titles = {c["title"] for c in convs}
        assert titles == {"thread A", "thread B"}

    def test_history_returns_messages_for_conversation(self, admin_client, ai_session):
        conv = AiConversation(user_id=1, book_id=7, title="my thread")
        ai_session.add(conv)
        ai_session.commit()
        m1 = AiMessage(conversation_id=conv.id, role="user", content="q1")
        m2 = AiMessage(conversation_id=conv.id, role="assistant", content="a1")
        ai_session.add_all([m1, m2])
        ai_session.commit()

        rv = admin_client.get("/ai/history/%d" % conv.id)
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["conversation"]["title"] == "my thread"
        assert [m["content"] for m in data["messages"]] == ["q1", "a1"]

    def test_get_memory(self, admin_client, ai_session):
        m = AiUserMemory(user_id=1, content="Likes sci-fi", source_book_id=1)
        ai_session.add(m)
        ai_session.commit()

        rv = admin_client.get("/ai/memory")
        assert rv.status_code == 200
        data = rv.get_json()
        assert "Likes sci-fi" in data["memories"]

    def test_history_requires_auth(self, client):
        rv = client.get("/ai/history/1")
        # With anonymous browsing enabled (calibre-web default), an anonymous
        # user gets 200 but with empty data. Otherwise they get redirected (302).
        if rv.status_code == 200:
            data = rv.get_json()
            assert data["messages"] == []
        else:
            assert rv.status_code in (301, 302, 401, 403)
