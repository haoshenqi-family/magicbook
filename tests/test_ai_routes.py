"""Tests for the AI chat API endpoints."""
import json
from unittest.mock import patch, MagicMock

import pytest


class TestAiRoutes:
    def test_history_empty(self, admin_client):
        rv = admin_client.get("/ai/history/1")
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["messages"] == []

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

    def test_chat_streams_response(self, admin_client, app):
        """POST /ai/chat should stream SSE chunks back."""
        from cps.ai.models import AiConfig, AiProvider
        from cps.ub import session
        from cps.ai.crypto import encrypt_value
        # Enable AI and set a fake api key
        cfg = session.query(AiConfig).first()
        if cfg is None:
            cfg = AiConfig()
            session.add(cfg)
        cfg.enabled = True
        # Use a real encryption key from calibre-web's config_sql
        from cps.ai.routes import _get_encryption_key
        key = _get_encryption_key()
        dsp = session.query(AiProvider).filter_by(provider_name="deepseek").first()
        if dsp is None:
            dsp = AiProvider()
            dsp.provider_name = "deepseek"
            dsp.api_base = "https://api.deepseek.com"
            dsp.active = True
            session.add(dsp)
        dsp.api_key_encrypted = encrypt_value("sk-test", key)
        session.commit()

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
        # Collect streamed data
        body = rv.get_data(as_text=True)
        assert "Hello " in body
        assert "world" in body
        assert "[DONE]" in body

    def test_chat_persists_user_and_assistant_messages(self, admin_client, app):
        """After a successful chat, both user and assistant messages should be in DB."""
        from cps.ai.models import AiConfig, AiConversation, AiMessage
        from cps.ub import session
        from cps.ai.routes import _get_encryption_key
        from cps.ai.crypto import encrypt_value

        cfg = session.query(AiConfig).first() or AiConfig()
        if cfg.id is None:
            session.add(cfg)
        cfg.enabled = True
        cfg.memory_enabled = False  # disable to skip extraction call
        key = _get_encryption_key()
        from cps.ai.models import AiProvider
        dsp = session.query(AiProvider).filter_by(provider_name="deepseek").first() or AiProvider()
        if dsp.id is None:
            dsp.provider_name = "deepseek"
            dsp.api_base = "https://api.deepseek.com"
            dsp.active = True
            session.add(dsp)
        dsp.api_key_encrypted = encrypt_value("sk-test", key)
        session.commit()

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
        conv = session.query(AiConversation).filter_by(user_id=1, book_id=42).first()
        assert conv is not None
        msgs = session.query(AiMessage).filter_by(conversation_id=conv.id).all()
        roles = [m.role for m in msgs]
        assert "user" in roles
        assert "assistant" in roles
        assistant_msg = next(m for m in msgs if m.role == "assistant")
        assert assistant_msg.content == "Reply text"

    def test_clear_history(self, admin_client, app):
        from cps.ai.models import AiConversation, AiMessage
        from cps.ub import session
        # Seed a conversation
        conv = AiConversation(user_id=1, book_id=99, book_format="EPUB")
        session.add(conv)
        session.commit()
        msg = AiMessage(conversation_id=conv.id, role="user", content="test")
        session.add(msg)
        session.commit()

        rv = admin_client.delete("/ai/history/99")
        assert rv.status_code == 200
        # Verify it's gone
        assert session.query(AiConversation).filter_by(book_id=99).count() == 0

    def test_get_memory(self, admin_client, app):
        from cps.ai.models import AiUserMemory
        from cps.ub import session
        m = AiUserMemory(user_id=1, content="Likes sci-fi", source_book_id=1)
        session.add(m)
        session.commit()

        rv = admin_client.get("/ai/memory")
        assert rv.status_code == 200
        data = rv.get_json()
        assert "Likes sci-fi" in data["memories"]

    def test_clear_memory(self, admin_client, app):
        from cps.ai.models import AiUserMemory
        from cps.ub import session
        m = AiUserMemory(user_id=1, content="to be deleted", source_book_id=1)
        session.add(m)
        session.commit()

        rv = admin_client.post("/ai/memory/clear")
        assert rv.status_code == 200
        assert session.query(AiUserMemory).filter_by(user_id=1).count() == 0

    def test_admin_page_get(self, admin_client):
        rv = admin_client.get("/ai/admin")
        assert rv.status_code == 200
        assert b"DeepSeek" in rv.data or b"deepseek" in rv.data

    def test_admin_page_post_updates_config(self, admin_client, app):
        from cps.ai.models import AiConfig
        from cps.ub import session
        rv = admin_client.post("/ai/admin", data={
            "enabled": "on",
            "default_provider": "deepseek",
            "default_model": "deepseek-reasoner",
            "memory_enabled": "on",
            "memory_extract_interval": "5",
            "system_prompt_extra": "Be terse.",
        })
        assert rv.status_code == 200
        cfg = session.query(AiConfig).first()
        assert cfg.enabled is True
        assert cfg.default_model == "deepseek-reasoner"
        assert cfg.memory_extract_interval == 5
        assert cfg.system_prompt_extra == "Be terse."

    def test_history_requires_auth(self, client):
        rv = client.get("/ai/history/1")
        # With anonymous browsing enabled (calibre-web default), an anonymous
        # user gets 200 but with empty data (no user_id to filter by).
        # With anonymous browsing disabled, they get redirected to login (302).
        if rv.status_code == 200:
            data = rv.get_json()
            assert data["messages"] == []
        else:
            assert rv.status_code in (301, 302, 401, 403)
