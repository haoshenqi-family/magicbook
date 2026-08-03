"""SQLAlchemy models for AI reading companion data.

Why an independent base:
- These tables used to inherit calibre-web's ``ub.Base`` (stored in the same
  SQLite ``app.db``). They now live on their own ``AiBase`` so AI data can be
  pointed at a separate database (MySQL via ``AI_DATABASE_URL`` in ``.env``)
  without mixing with the calibre library / user data.
- Because the AI database is independent, ``user_id`` is a plain integer with
  no FK to calibre-web's ``user`` table (that table only exists in the SQLite
  app.db). Ownership is enforced at the application layer.

Tables:
  ai_config        — singleton row of global AI settings (enabled, defaults)
  ai_provider      — per-provider config (api_base, encrypted api_key, models JSON)
  ai_conversation  — one chat thread per (user, book); a book may have many
  ai_message       — individual messages in a conversation
  ai_user_memory   — cross-book long-term memory entries extracted from conversations

All String columns carry an explicit length because MySQL requires one
(SQLAlchemy's bare ``String`` fails on MySQL at DDL time).
"""
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, Text,
                        ForeignKey)
from sqlalchemy.orm import relationship

from .database import AiBase
from .timezone import now as _now


def _utcnow():
    # 中国大陆时区（北京时间）——见 cps/ai/timezone.py 说明
    return _now()


class AiConfig(AiBase):
    """Singleton row of global AI companion settings."""

    __tablename__ = "ai_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    default_provider = Column(String(50), default="deepseek")
    default_model = Column(String(100), default="deepseek-chat")
    memory_enabled = Column(Boolean, default=True)
    memory_extract_interval = Column(Integer, default=10)  # extract after every N messages
    system_prompt_extra = Column(Text, default="")


class AiProvider(AiBase):
    """Per-provider configuration (api_base, encrypted api_key, models JSON).

    The same table is used for AI providers (deepseek, ...) and the Authentik
    OAuth provider. For Authentik, ``models_json`` stores a JSON object with
    ``{"client_secret_encrypted": "..."}`` instead of a model list.
    """

    __tablename__ = "ai_provider"

    id = Column(Integer, primary_key=True)
    provider_name = Column(String(100), unique=True)
    display_name = Column(String(100), default="")
    api_base = Column(String(500), default="")
    api_key_encrypted = Column(String(1000), default="")
    models_json = Column(Text, default="[]")  # JSON array of {"id","label"}
    active = Column(Boolean, default=False)


class AiConversation(AiBase):
    """One chat thread for a (user, book) pair — a book may have many threads."""

    __tablename__ = "ai_conversation"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)  # no FK: AI DB has no calibre user table
    book_id = Column(Integer, index=True)
    book_format = Column(String(20), default="")
    title = Column(String(500), default="")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    messages = relationship("AiMessage", backref="conversation",
                            cascade="all, delete-orphan", lazy="dynamic")


class AiMessage(AiBase):
    """Individual messages in a conversation."""

    __tablename__ = "ai_message"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversation.id"), index=True)
    role = Column(String(20))  # "user" | "assistant" | "system"
    content = Column(Text)
    page_context = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)


class AiUserMemory(AiBase):
    """Cross-book long-term memory entries extracted from conversations."""

    __tablename__ = "ai_user_memory"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)  # no FK: see AiConversation.user_id
    content = Column(Text)
    source_book_id = Column(Integer, default=None)
    created_at = Column(DateTime, default=_utcnow)
