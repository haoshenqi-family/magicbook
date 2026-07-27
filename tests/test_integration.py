"""End-to-end integration tests for the AI reading companion.

Exercises the full chat flow against the real Flask app + DB, mocking only
the outbound LLM HTTP call (``get_active_provider``). Verifies:

  1. Admin configures provider & enables AI via the admin page.
  2. User sends a chat message and receives a streamed SSE reply.
  3. Conversation + messages are persisted to the DB.
  4. History endpoint returns the saved messages.
  5. After N messages, memory extraction runs and stores a long-term memory.
  6. The extracted memory is injected into the system prompt of a later call.
  7. Clearing history and memory works end-to-end.
"""
import json
from unittest.mock import patch, MagicMock

import pytest


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


def _enable_ai(app):
    """Flip the AiConfig + deepseek provider rows to a usable state.

    The per-test ``app`` fixture deletes all AiProvider rows for isolation,
    and seed_default_config() only runs once per session, so we must
    re-create the deepseek provider row here.
    """
    from cps.ai.models import AiConfig, AiProvider
    from cps.ub import session
    from cps.ai.routes import _get_encryption_key
    from cps.ai.crypto import encrypt_value

    key = _get_encryption_key()
    cfg = session.query(AiConfig).first()
    if cfg is None:
        cfg = AiConfig()
        session.add(cfg)
    cfg.enabled = True
    cfg.memory_enabled = True
    cfg.memory_extract_interval = 4  # trigger extraction after 4 messages (2 turns)
    cfg.system_prompt_extra = ""

    dsp = session.query(AiProvider).filter_by(provider_name="deepseek").first()
    if dsp is None:
        dsp = AiProvider(provider_name="deepseek",
                         api_base="https://api.deepseek.com", active=True)
        session.add(dsp)
    dsp.active = True
    dsp.api_key_encrypted = encrypt_value("sk-test-integration", key)
    session.commit()
    return cfg


def _consume_stream(rv):
    """Read a streamed Response fully and return the concatenated SSE text."""
    return rv.get_data(as_text=True)


def _parse_deltas(body):
    """Pull the ``delta`` values out of an SSE body, ignoring [DONE]/errors."""
    deltas = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("data: "):
            continue
        payload = line[len("data: "):]
        if payload == "[DONE]":
            continue
        try:
            obj = json.loads(payload)
        except ValueError:
            continue
        if "delta" in obj:
            deltas.append(obj["delta"])
    return "".join(deltas)


class TestEndToEnd:
    def test_full_chat_flow_with_memory(self, admin_client, app):
        """Configure -> chat -> history -> memory extraction -> memory reuse."""
        from cps.ai.models import (AiConfig, AiConversation, AiMessage,
                                   AiUserMemory)
        from cps.ub import session

        # 1) Set up AI config + provider (the app fixture wipes providers
        #    per-test, and seed_default_config only runs once per session).
        _enable_ai(app)

        # Verify the admin page can also update config end-to-end.
        _ensure_db_configured()
        rv = admin_client.post("/ai/admin", data={
            "enabled": "on",
            "memory_enabled": "on",
            "default_provider": "deepseek",
            "default_model": "deepseek-chat",
            "memory_extract_interval": "4",
            "system_prompt_extra": "Be concise.",
        })
        assert rv.status_code == 200
        cfg = session.query(AiConfig).first()
        assert cfg.enabled is True
        assert cfg.memory_extract_interval == 4

        # 2) First user message — provider returns a normal reply.
        chat_provider = MagicMock()
        chat_provider.chat.return_value = iter(["This book ", "is about AI."])

        _ensure_db_configured()
        with patch("cps.ai.routes.get_active_provider",
                   return_value=(chat_provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 7,
                "book_format": "EPUB",
                "message": "What is this book about?",
                "page_context": "Chapter 1: Introduction to machine learning.",
                "book_title": "Machine Learning Basics",
                "book_authors": ["Jane Doe"],
                "book_tags": ["AI", "education"],
            })
        assert rv.status_code == 200
        body = _consume_stream(rv)
        assert "This book " in body and "is about AI." in body
        assert "[DONE]" in body

        # 3) History endpoint returns the saved user + assistant messages.
        _ensure_db_configured()
        rv = admin_client.get("/ai/history/7")
        assert rv.status_code == 200
        msgs = rv.get_json()["messages"]
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "What is this book about?"
        assert msgs[1]["role"] == "assistant"
        assert msgs[1]["content"] == "This book is about AI."

        # 4) Second turn (messages 3 & 4) — hits the extract interval (4),
        #    so the memory-extraction path runs. We make the provider serve
        #    BOTH the chat reply (stream) and the extraction call (non-stream).
        def fake_chat(messages, model, stream=True, **kwargs):
            if stream:
                return iter(["Great question. ", "See chapter 2."])
            # Non-stream call == memory extraction
            return "User is interested in machine learning concepts."

        chat_provider.chat.side_effect = fake_chat

        _ensure_db_configured()
        with patch("cps.ai.routes.get_active_provider",
                   return_value=(chat_provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 7,
                "message": "Tell me more about chapter 2.",
                "page_context": "Chapter 2: Neural networks.",
                "book_title": "Machine Learning Basics",
            })
        assert rv.status_code == 200
        _consume_stream(rv)

        # 5) A long-term memory entry should now exist for this user.
        mems = session.query(AiUserMemory).filter_by(user_id=1).all()
        assert len(mems) >= 1
        assert "machine learning" in mems[0].content.lower()

        # 6) The memory is injected into the system prompt of the NEXT call.
        #    We capture the messages list the provider receives to verify.
        captured = {}

        def capturing_chat(messages, model, stream=True, **kwargs):
            captured["messages"] = list(messages)
            if stream:
                return iter(["Noted."])
            return "NONE"

        chat_provider.chat.side_effect = capturing_chat
        _ensure_db_configured()
        with patch("cps.ai.routes.get_active_provider",
                   return_value=(chat_provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 7,
                "message": "Thanks.",
                "page_context": "",
                "book_title": "Machine Learning Basics",
            })
        assert rv.status_code == 200
        _consume_stream(rv)

        system_msg = next(m for m in captured["messages"] if m["role"] == "system")
        assert "machine learning" in system_msg["content"].lower()
        # Book metadata is also in the system prompt
        assert "Machine Learning Basics" in system_msg["content"]

    def test_clear_history_then_chat_starts_fresh(self, admin_client, app):
        """After clearing history, a new chat has no prior messages."""
        _enable_ai(app)
        from cps.ub import session
        from cps.ai.models import AiConversation, AiMessage

        # Seed a conversation directly
        conv = AiConversation(user_id=1, book_id=55, book_format="EPUB",
                              title="Seeded")
        session.add(conv)
        session.commit()
        session.add(AiMessage(conversation_id=conv.id, role="user",
                              content="old question"))
        session.add(AiMessage(conversation_id=conv.id, role="assistant",
                              content="old answer"))
        session.commit()

        # Clear via the API
        _ensure_db_configured()
        rv = admin_client.delete("/ai/history/55")
        assert rv.status_code == 200
        assert session.query(AiConversation).filter_by(book_id=55).count() == 0

        # New chat — history endpoint should be empty before the call
        _ensure_db_configured()
        rv = admin_client.get("/ai/history/55")
        assert rv.get_json()["messages"] == []

        provider = MagicMock()
        provider.chat.return_value = iter(["Fresh reply."])
        _ensure_db_configured()
        with patch("cps.ai.routes.get_active_provider",
                   return_value=(provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 55,
                "message": "New question",
                "page_context": "",
            })
        assert rv.status_code == 200
        _consume_stream(rv)

        _ensure_db_configured()
        rv = admin_client.get("/ai/history/55")
        assert rv.status_code == 200
        msgs = rv.get_json()["messages"]
        assert len(msgs) == 2
        assert msgs[0]["content"] == "New question"
        assert msgs[1]["content"] == "Fresh reply."

    def test_memory_clear_endpoint(self, admin_client, app):
        """POST /ai/memory/clear wipes all long-term memory for the user."""
        from cps.ub import session
        from cps.ai.models import AiUserMemory

        session.add(AiUserMemory(user_id=1, content="likes sci-fi",
                                 source_book_id=1))
        session.add(AiUserMemory(user_id=1, content="prefers concise answers",
                                 source_book_id=2))
        session.commit()
        assert session.query(AiUserMemory).filter_by(user_id=1).count() == 2

        _ensure_db_configured()
        rv = admin_client.post("/ai/memory/clear")
        assert rv.status_code == 200
        assert session.query(AiUserMemory).filter_by(user_id=1).count() == 0

        # GET /ai/memory reflects the cleared state
        _ensure_db_configured()
        rv = admin_client.get("/ai/memory")
        assert rv.status_code == 200
        assert rv.get_json()["memories"] == []

    def test_disabled_ai_returns_503(self, admin_client, app):
        """When AI is disabled, /ai/chat returns 503 (no provider call)."""
        from cps.ub import session
        from cps.ai.models import AiConfig
        cfg = session.query(AiConfig).first()
        assert cfg is not None
        cfg.enabled = False
        session.commit()

        _ensure_db_configured()
        rv = admin_client.post("/ai/chat", json={
            "book_id": 1,
            "message": "hello",
        })
        assert rv.status_code == 503

    def test_book_metadata_in_system_prompt(self, admin_client, app):
        """The system prompt sent to the provider includes book metadata."""
        _enable_ai(app)
        captured = {}
        provider = MagicMock()

        def chat(messages, model, stream=True, **kwargs):
            captured["messages"] = list(messages)
            return iter(["ok"])

        provider.chat.side_effect = chat

        _ensure_db_configured()
        with patch("cps.ai.routes.get_active_provider",
                   return_value=(provider, "deepseek-chat")):
            rv = admin_client.post("/ai/chat", json={
                "book_id": 99,
                "book_format": "EPUB",
                "message": "Explain this page.",
                "page_context": "The quick brown fox jumps over the lazy dog.",
                "book_title": "Typography Tales",
                "book_authors": ["A. Author", "B. Coauthor"],
                "book_description": "<p>A book about fonts and type.</p>",
                "book_tags": ["design", "typography"],
            })
        assert rv.status_code == 200
        _consume_stream(rv)

        system_msg = next(m for m in captured["messages"] if m["role"] == "system")
        assert "Typography Tales" in system_msg["content"]
        assert "A. Author" in system_msg["content"]
        assert "design" in system_msg["content"]
        # HTML stripped from description
        assert "<p>" not in system_msg["content"]
        assert "fonts and type" in system_msg["content"]
        # Page context included
        assert "quick brown fox" in system_msg["content"]
