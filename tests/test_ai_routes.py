"""Tests for the AI chat API endpoints (multi-conversation)."""
import json
from unittest.mock import patch, MagicMock

import pytest

from cps.ai.models import (AiConfig, AiProvider, AiConversation, AiMessage,
                           AiUserMemory)


def _enable_ai(ai_session):
    """Enable AI and set a fake DeepSeek api key so get_active_provider works."""
    from cps.ai.routes import _get_encryption_key
    from cps.ai.crypto import encrypt_value
    cfg = ai_session.query(AiConfig).first()
    if cfg is None:
        cfg = AiConfig()
        ai_session.add(cfg)
    cfg.enabled = True
    cfg.memory_enabled = False
    key = _get_encryption_key()
    dsp = ai_session.query(AiProvider).filter_by(provider_name="deepseek").first()
    if dsp is None:
        dsp = AiProvider()
        dsp.provider_name = "deepseek"
        dsp.api_base = "https://api.deepseek.com"
        dsp.active = True
        ai_session.add(dsp)
    dsp.api_key_encrypted = encrypt_value("sk-test", key)
    ai_session.commit()
    return key


class TestAiRoutes:
    def test_history_empty_for_unknown_conversation(self, admin_client):
        rv = admin_client.get("/ai/history/999999")
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["messages"] == []
        assert data["conversation"] is None

    def test_chat_requires_book_id(self, admin_client):
        rv = admin_client.post("/ai/chat", json={})
        assert rv.status_code == 400

    def test_chat_requires_message(self, admin_client):
        rv = admin_client.post("/ai/chat", json={"book_id": 1})
        assert rv.status_code == 400

    def test_chat_returns_503_when_disabled(self, admin_client):
        # AI is disabled by default (conftest resets config)
        rv = admin_client.post("/ai/chat", json={
            "book_id": 1,
            "message": "hello",
            "page_context": "page text",
        })
        assert rv.status_code == 503

    def test_chat_streams_response(self, admin_client, ai_session):
        """POST /ai/chat should stream SSE chunks back."""
        _enable_ai(ai_session)

        fake_provider = MagicMock()
        fake_provider.chat.return_value = iter(["Hello ", "world"])

        with patch("cps.ai.routes.get_active_provider", return_value=(fake_provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 1,
                "book_format": "EPUB",
                "message": "What is this book about?",
                "page_context": "Chapter 1 text...",
            })

        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "Hello " in body
        assert "world" in body
        assert "[DONE]" in body

    def test_chat_persists_user_and_assistant_messages(self, admin_client, ai_session):
        """After a successful chat, both user and assistant messages should be in DB."""
        _enable_ai(ai_session)

        fake_provider = MagicMock()
        fake_provider.chat.return_value = iter(["Reply text"])

        with patch("cps.ai.routes.get_active_provider", return_value=(fake_provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 42,
                "book_format": "EPUB",
                "message": "What is this book about?",
                "page_context": "Chapter 1 text...",
            })
        assert rv.status_code == 200
        # Consume the full stream so the generator's post-yield code
        # (which persists the assistant message) actually runs.
        rv.get_data(as_text=True)

        # Verify messages persisted
        conv = ai_session.query(AiConversation).filter_by(user_id=1, book_id=42).first()
        assert conv is not None
        msgs = ai_session.query(AiMessage).filter_by(conversation_id=conv.id).all()
        roles = [m.role for m in msgs]
        assert "user" in roles
        assert "assistant" in roles
        assistant_msg = next(m for m in msgs if m.role == "assistant")
        assert assistant_msg.content == "Reply text"

    def test_chat_autonames_conversation_from_first_question(self, admin_client, ai_session):
        """The thread title should be derived from the first user question."""
        _enable_ai(ai_session)
        fake_provider = MagicMock()
        fake_provider.chat.return_value = iter(["ok"])
        with patch("cps.ai.routes.get_active_provider", return_value=(fake_provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 42,
                "message": "Summarize the plot of this story",
            })
        rv.get_data(as_text=True)
        conv = ai_session.query(AiConversation).filter_by(user_id=1, book_id=42).first()
        assert conv is not None
        assert "Summarize the plot" in conv.title

    def test_chat_autonames_even_with_book_title_present(self, admin_client, ai_session):
        """Auto-naming must NOT be defeated by a non-empty book_title.

        The frontend always sends book_title, so threads would otherwise all
        show the book title instead of the user's first question.
        """
        _enable_ai(ai_session)
        fake_provider = MagicMock()
        fake_provider.chat.return_value = iter(["ok"])
        with patch("cps.ai.routes.get_active_provider", return_value=(fake_provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 42,
                "book_title": "Some Book Title",
                "message": "Who is the hero",
            })
        rv.get_data(as_text=True)
        conv = ai_session.query(AiConversation).filter_by(user_id=1, book_id=42).first()
        assert conv is not None
        assert "Who is the hero" in conv.title
        # ...and NOT the book title
        assert "Some Book Title" not in conv.title

    def test_conversations_ordered_by_recent_activity(self, admin_client, ai_session):
        """Conversations list should order by most recently active."""
        _enable_ai(ai_session)
        from datetime import datetime, timezone

        c1 = AiConversation(user_id=1, book_id=42, title="older",
                            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        c2 = AiConversation(user_id=1, book_id=42, title="newer",
                            updated_at=datetime(2026, 2, 1, tzinfo=timezone.utc))
        ai_session.add_all([c1, c2])
        ai_session.commit()

        rv = admin_client.get("/ai/conversations/42")
        titles = [c["title"] for c in rv.get_json()["conversations"]]
        assert titles == ["newer", "older"]

    def test_new_conversation_creates_thread(self, admin_client, ai_session):
        rv = admin_client.post("/ai/conversations/7",
                               json={"book_format": "EPUB"})
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["conversation_id"] is not None
        conv = ai_session.query(AiConversation).filter_by(id=data["conversation_id"]).first()
        assert conv is not None
        assert conv.user_id == 1
        assert conv.book_id == 7
        assert conv.book_format == "EPUB"

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

    def test_chat_with_existing_conversation_id(self, admin_client, ai_session):
        _enable_ai(ai_session)
        conv = AiConversation(user_id=1, book_id=42, title="existing")
        ai_session.add(conv)
        ai_session.commit()
        conv_id = conv.id  # capture before requests detach the instance
        m = AiMessage(conversation_id=conv_id, role="user", content="earlier question")
        ai_session.add(m)
        ai_session.commit()

        fake_provider = MagicMock()
        fake_provider.chat.return_value = iter(["follow-up reply"])
        with patch("cps.ai.routes.get_active_provider", return_value=(fake_provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 42,
                "conversation_id": conv_id,
                "message": "tell me more",
            })
        assert rv.status_code == 200
        rv.get_data(as_text=True)

        # Same conversation, no duplicate thread
        assert ai_session.query(AiConversation).filter_by(user_id=1, book_id=42).count() == 1
        msgs = ai_session.query(AiMessage).filter_by(conversation_id=conv_id)\
            .order_by(AiMessage.created_at.asc()).all()
        contents = [m.content for m in msgs]
        assert "earlier question" in contents
        assert "tell me more" in contents

    def test_chat_rejects_conversation_owned_by_other_user(self, admin_client, ai_session):
        _enable_ai(ai_session)
        other = AiConversation(user_id=99, book_id=42, title="not mine")
        ai_session.add(other)
        ai_session.commit()

        fake_provider = MagicMock()
        fake_provider.chat.return_value = iter(["x"])
        with patch("cps.ai.routes.get_active_provider", return_value=(fake_provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 42,
                "conversation_id": other.id,
                "message": "hello",
            })
        # Ownership guard: must not stream into someone else's thread.
        assert rv.status_code == 404
        assert ai_session.query(AiConversation).filter_by(id=other.id).count() == 1

    def test_chat_rejects_conversation_for_different_book(self, admin_client, ai_session):
        _enable_ai(ai_session)
        conv = AiConversation(user_id=1, book_id=10, title="different book")
        ai_session.add(conv)
        ai_session.commit()

        fake_provider = MagicMock()
        fake_provider.chat.return_value = iter(["x"])
        with patch("cps.ai.routes.get_active_provider", return_value=(fake_provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 42,
                "conversation_id": conv.id,
                "message": "hello",
            })
        assert rv.status_code == 404

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

    def test_clear_conversation_deletes_thread_and_messages(self, admin_client, ai_session):
        conv = AiConversation(user_id=1, book_id=99, book_format="EPUB")
        ai_session.add(conv)
        ai_session.commit()
        msg = AiMessage(conversation_id=conv.id, role="user", content="test")
        ai_session.add(msg)
        ai_session.commit()

        rv = admin_client.delete("/ai/history/%d" % conv.id)
        assert rv.status_code == 200
        assert ai_session.query(AiConversation).filter_by(id=conv.id).count() == 0
        assert ai_session.query(AiMessage).filter_by(conversation_id=conv.id).count() == 0

    def test_get_memory(self, admin_client, ai_session):
        m = AiUserMemory(user_id=1, content="Likes sci-fi", source_book_id=1)
        ai_session.add(m)
        ai_session.commit()

        rv = admin_client.get("/ai/memory")
        assert rv.status_code == 200
        data = rv.get_json()
        assert "Likes sci-fi" in data["memories"]

    def test_clear_memory(self, admin_client, ai_session):
        m = AiUserMemory(user_id=1, content="to be deleted", source_book_id=1)
        ai_session.add(m)
        ai_session.commit()

        rv = admin_client.post("/ai/memory/clear")
        assert rv.status_code == 200
        assert ai_session.query(AiUserMemory).filter_by(user_id=1).count() == 0

    def test_admin_page_get(self, admin_client):
        rv = admin_client.get("/ai/admin")
        assert rv.status_code == 200
        assert b"DeepSeek" in rv.data or b"deepseek" in rv.data

    def test_admin_page_post_updates_config(self, admin_client, ai_session):
        rv = admin_client.post("/ai/admin", data={
            "enabled": "on",
            "default_provider": "deepseek",
            "default_model": "deepseek-reasoner",
            "memory_enabled": "on",
            "memory_extract_interval": "5",
            "system_prompt_extra": "Be terse.",
        })
        assert rv.status_code == 200
        cfg = ai_session.query(AiConfig).first()
        assert cfg.enabled is True
        assert cfg.default_model == "deepseek-reasoner"
        assert cfg.memory_extract_interval == 5
        assert cfg.system_prompt_extra == "Be terse."

    def test_history_requires_auth(self, client):
        rv = client.get("/ai/history/1")
        # With anonymous browsing enabled (calibre-web default), an anonymous
        # user gets 200 but with empty data. Otherwise they get redirected (302).
        if rv.status_code == 200:
            data = rv.get_json()
            assert data["messages"] == []
        else:
            assert rv.status_code in (301, 302, 401, 403)
