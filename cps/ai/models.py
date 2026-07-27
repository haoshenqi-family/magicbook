"""SQLAlchemy models for AI reading companion data.

All models inherit from calibre-web's ``ub.Base`` so they are auto-created by
``Base.metadata.create_all(engine)`` on startup (see cps/ub.py:init_db). No
manual migration is needed for *new* tables — adding a new column would
require bumping the schema-version check, but adding new tables is automatic.

Tables:
  ai_config        — singleton row of global AI settings (enabled, defaults)
  ai_provider      — per-provider config (api_base, encrypted api_key, models JSON)
  ai_conversation  — one per (user, book) chat thread
  ai_message       — individual messages in a conversation
  ai_user_memory   — cross-book long-term memory entries extracted from conversations
"""
from datetime import datetime, timezone

from sqlalchemy import (Column, Integer, String, Boolean, DateTime, Text,
                        ForeignKey)
from sqlalchemy.orm import relationship

from cps.ub import Base


def _utcnow():
    return datetime.now(timezone.utc)


class AiConfig(Base):
    """Singleton row of global AI companion settings."""

    __tablename__ = "ai_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    default_provider = Column(String, default="deepseek")
    default_model = Column(String, default="deepseek-chat")
    memory_enabled = Column(Boolean, default=True)
    memory_extract_interval = Column(Integer, default=10)  # extract after every N messages
    system_prompt_extra = Column(Text, default="")


class AiProvider(Base):
    """Per-provider configuration (api_base, encrypted api_key, models JSON).

    The same table is used for AI providers (deepseek, ...) and the Authentik
    OAuth provider. For Authentik, ``models_json`` stores a JSON object with
    ``{"client_secret_encrypted": "..."}`` instead of a model list.
    """

    __tablename__ = "ai_provider"

    id = Column(Integer, primary_key=True)
    provider_name = Column(String, unique=True)
    display_name = Column(String, default="")
    api_base = Column(String, default="")
    api_key_encrypted = Column(String, default="")
    models_json = Column(Text, default="[]")  # JSON array of {"id","label"}
    active = Column(Boolean, default=False)


class AiConversation(Base):
    """One chat thread per (user, book)."""

    __tablename__ = "ai_conversation"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    book_id = Column(Integer)
    book_format = Column(String, default="")
    title = Column(String, default="")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    messages = relationship("AiMessage", backref="conversation",
                            cascade="all, delete-orphan", lazy="dynamic")


class AiMessage(Base):
    """Individual messages in a conversation."""

    __tablename__ = "ai_message"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversation.id"))
    role = Column(String)  # "user" | "assistant" | "system"
    content = Column(Text)
    page_context = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)


class AiUserMemory(Base):
    """Cross-book long-term memory entries extracted from conversations."""

    __tablename__ = "ai_user_memory"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    content = Column(Text)
    source_book_id = Column(Integer, default=None)
    created_at = Column(DateTime, default=_utcnow)
