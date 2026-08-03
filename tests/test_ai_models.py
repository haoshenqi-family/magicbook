"""Tests for AI SQLAlchemy models.

Note: SQLAlchemy ``Column(default=...)`` only applies the default at flush
time (when the row is actually INSERTed), not at Python construction time.
So tests that assert default values must add the object to a session and
commit (or at least flush) first.

AI models live on their own AiBase bound to the AI data layer (sqlite in
tests), so all DB operations go through the ``ai_session`` fixture.
"""
import pytest

from cps.ai.models import (
    AiConfig, AiProvider, AiConversation, AiMessage, AiUserMemory,
)


class TestAiModels:
    def test_ai_config_defaults(self, app, ai_session):
        cfg = AiConfig()
        ai_session.add(cfg)
        ai_session.commit()
        # Re-load to confirm defaults were applied at flush
        loaded = ai_session.query(AiConfig).filter_by(id=cfg.id).first()
        assert loaded.enabled is False
        assert loaded.default_provider == "deepseek"
        assert loaded.default_model == "deepseek-chat"
        assert loaded.memory_enabled is True
        assert loaded.memory_extract_interval == 10
        assert loaded.system_prompt_extra == ""

    def test_ai_provider_columns(self, app, ai_session):
        p = AiProvider()
        p.provider_name = "deepseek"
        p.api_base = "https://api.deepseek.com"
        p.api_key_encrypted = "enc-token"
        p.models_json = '[{"id":"deepseek-chat","label":"DeepSeek Chat"}]'
        p.active = True
        ai_session.add(p)
        ai_session.commit()
        loaded = ai_session.query(AiProvider).filter_by(provider_name="deepseek").first()
        assert loaded.provider_name == "deepseek"
        assert loaded.active is True
        # display_name has a server-side default of ""
        assert loaded.display_name == ""

    def test_ai_conversation_message_relationship(self, app, ai_session):
        conv = AiConversation(user_id=1, book_id=42)
        ai_session.add(conv)
        ai_session.commit()
        msg = AiMessage(conversation_id=conv.id, role="user",
                        content="What is this book about?", page_context="chapter 1 text")
        ai_session.add(msg)
        ai_session.commit()
        assert conv.id is not None
        assert msg.id is not None
        assert msg.conversation_id == conv.id
        # Verify the relationship works
        msgs = conv.messages.all()
        assert len(msgs) == 1
        assert msgs[0].content == "What is this book about?"

    def test_ai_user_memory(self, app, ai_session):
        m = AiUserMemory()
        m.user_id = 1
        m.content = "User prefers concise explanations"
        m.source_book_id = 42
        ai_session.add(m)
        ai_session.commit()
        loaded = ai_session.query(AiUserMemory).filter_by(id=m.id).first()
        assert loaded.user_id == 1
        assert loaded.source_book_id == 42
        assert loaded.content == "User prefers concise explanations"
        assert loaded.created_at is not None

    def test_ai_message_defaults(self, app, ai_session):
        msg = AiMessage(role="assistant", content="Hello")
        ai_session.add(msg)
        ai_session.commit()
        loaded = ai_session.query(AiMessage).filter_by(id=msg.id).first()
        assert loaded.role == "assistant"
        assert loaded.content == "Hello"
        assert loaded.page_context == ""
        assert loaded.created_at is not None

    def test_conversation_cascade_deletes_messages(self, app, ai_session):
        conv = AiConversation(user_id=1, book_id=77)
        ai_session.add(conv)
        ai_session.commit()
        m1 = AiMessage(conversation_id=conv.id, role="user", content="q1")
        m2 = AiMessage(conversation_id=conv.id, role="assistant", content="a1")
        ai_session.add_all([m1, m2])
        ai_session.commit()
        assert ai_session.query(AiMessage).filter_by(conversation_id=conv.id).count() == 2

        ai_session.delete(conv)
        ai_session.commit()
        # Cascade should have removed the messages
        assert ai_session.query(AiMessage).filter_by(conversation_id=conv.id).count() == 0

    def test_multiple_conversations_per_book(self, app, ai_session):
        """A book may have many independent conversation threads."""
        c1 = AiConversation(user_id=1, book_id=5, title="First")
        c2 = AiConversation(user_id=1, book_id=5, title="Second")
        c3 = AiConversation(user_id=2, book_id=5, title="Another user")
        ai_session.add_all([c1, c2, c3])
        ai_session.commit()

        mine = ai_session.query(AiConversation).filter_by(user_id=1, book_id=5).all()
        assert len(mine) == 2
        assert {c.title for c in mine} == {"First", "Second"}
