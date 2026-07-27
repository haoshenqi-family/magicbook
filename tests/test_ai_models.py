"""Tests for AI SQLAlchemy models.

Note: SQLAlchemy ``Column(default=...)`` only applies the default at flush
time (when the row is actually INSERTed), not at Python construction time.
So tests that assert default values must add the object to a session and
commit (or at least flush) first.
"""
import pytest

from cps.ai.models import (
    AiConfig, AiProvider, AiConversation, AiMessage, AiUserMemory,
)


class TestAiModels:
    def test_ai_config_defaults(self, app):
        from cps.ub import session
        cfg = AiConfig()
        session.add(cfg)
        session.commit()
        # Re-load to confirm defaults were applied at flush
        loaded = session.query(AiConfig).filter_by(id=cfg.id).first()
        assert loaded.enabled is False
        assert loaded.default_provider == "deepseek"
        assert loaded.default_model == "deepseek-chat"
        assert loaded.memory_enabled is True
        assert loaded.memory_extract_interval == 10
        assert loaded.system_prompt_extra == ""

    def test_ai_provider_columns(self, app):
        from cps.ub import session
        p = AiProvider()
        p.provider_name = "deepseek"
        p.api_base = "https://api.deepseek.com"
        p.api_key_encrypted = "enc-token"
        p.models_json = '[{"id":"deepseek-chat","label":"DeepSeek Chat"}]'
        p.active = True
        session.add(p)
        session.commit()
        loaded = session.query(AiProvider).filter_by(provider_name="deepseek").first()
        assert loaded.provider_name == "deepseek"
        assert loaded.active is True
        # display_name has a server-side default of ""
        assert loaded.display_name == ""

    def test_ai_conversation_message_relationship(self, app):
        from cps.ub import session
        conv = AiConversation(user_id=1, book_id=42)
        session.add(conv)
        session.commit()
        msg = AiMessage(conversation_id=conv.id, role="user",
                        content="What is this book about?", page_context="chapter 1 text")
        session.add(msg)
        session.commit()
        assert conv.id is not None
        assert msg.id is not None
        assert msg.conversation_id == conv.id
        # Verify the relationship works
        msgs = conv.messages.all()
        assert len(msgs) == 1
        assert msgs[0].content == "What is this book about?"

    def test_ai_user_memory(self, app):
        from cps.ub import session
        m = AiUserMemory()
        m.user_id = 1
        m.content = "User prefers concise explanations"
        m.source_book_id = 42
        session.add(m)
        session.commit()
        loaded = session.query(AiUserMemory).filter_by(id=m.id).first()
        assert loaded.user_id == 1
        assert loaded.source_book_id == 42
        assert loaded.content == "User prefers concise explanations"
        assert loaded.created_at is not None

    def test_ai_message_defaults(self, app):
        from cps.ub import session
        msg = AiMessage(role="assistant", content="Hello")
        session.add(msg)
        session.commit()
        loaded = session.query(AiMessage).filter_by(id=msg.id).first()
        assert loaded.role == "assistant"
        assert loaded.content == "Hello"
        assert loaded.page_context == ""
        assert loaded.created_at is not None

    def test_conversation_cascade_deletes_messages(self, app):
        from cps.ub import session
        conv = AiConversation(user_id=1, book_id=77)
        session.add(conv)
        session.commit()
        m1 = AiMessage(conversation_id=conv.id, role="user", content="q1")
        m2 = AiMessage(conversation_id=conv.id, role="assistant", content="a1")
        session.add_all([m1, m2])
        session.commit()
        assert session.query(AiMessage).filter_by(conversation_id=conv.id).count() == 2

        session.delete(conv)
        session.commit()
        # Cascade should have removed the messages
        assert session.query(AiMessage).filter_by(conversation_id=conv.id).count() == 0
