# AI Reading Companion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an AI-assisted reading companion to a calibre-web fork: a floating chat sidebar inside each reader (epub/pdf/txt) that sends book metadata + current page text + user question to a configurable LLM provider (default DeepSeek), with persistent per-book conversation history and cross-book user memory, plus Authentik OAuth login as a new provider — all with minimal intrusion into upstream calibre-web code.

**Architecture:** All new code lives in an isolated `cps/ai/` subpackage (Python) plus a small set of new templates/JS/CSS assets. Upstream calibre-web is touched in only 6 places: 1 line added to `cps/main.py` (register blueprints), 1 line added to each of the 3 reader templates (`read.html`, `readpdf.html`, `readtxt.html`) to `{% include %}` the chat panel, 1 line in `layout.html` (optional admin link), and a `[tool.pytest.ini_options]` block added to `pyproject.toml`. AI provider configs, conversations, messages, and user memories are stored in new SQLAlchemy tables that reuse calibre-web's `ub.Base` (auto-created by `Base.metadata.create_all` on startup — no manual migration). Authentik uses flask-dance's generic `OAuth2ConsumerBlueprint` (flask-dance is already an optional dependency) and stores tokens in the existing `ub.OAuth` table.

**Tech Stack:**
- Python 3 / Flask (existing calibre-web stack)
- SQLAlchemy (existing) — new tables via `ub.Base`
- `requests` (already a dependency) — DeepSeek API calls with SSE streaming
- flask-dance (already optional dep) — Authentik OAuth2
- `cryptography.fernet` (already a dependency) — encrypt API keys at rest
- `markdown2` (already optional dep) — render AI markdown responses
- pytest (new dev dependency) — tests
- Vanilla JS + jQuery (already on reader pages) — chat panel frontend

---

## File Structure

### New files (all AI code isolated)

**Python — `cps/ai/` subpackage:**
- `cps/ai/__init__.py` — package init; `get_provider(name)` factory; seeds default config on import
- `cps/ai/base.py` — `BaseProvider` ABC and `ModelInfo` dataclass
- `cps/ai/deepseek.py` — `DeepSeekProvider` (OpenAI-compatible chat completions with SSE streaming)
- `cps/ai/registry.py` — provider registry; loads providers from DB config
- `cps/ai/models.py` — SQLAlchemy models: `AiConfig`, `AiProvider`, `AiConversation`, `AiMessage`, `AiUserMemory`
- `cps/ai/memory.py` — memory extraction (call AI to summarize insights) + retrieval (inject into system prompt)
- `cps/ai/routes.py` — `aichat` blueprint: `/ai/chat` (streaming), `/ai/history/<book_id>`, `/ai/history/<book_id>` (DELETE), `/ai/memory`, `/ai/memory/clear`, `/ai/admin` (GET/POST config)
- `cps/ai/authentik.py` — `register_authentik(app)`: builds `OAuth2ConsumerBlueprint`, wires `@oauth_authorized` signal, defines `/login/authentik` route
- `cps/ai/crypto.py` — `encrypt_value`/`decrypt_value` helpers using config encryption key

**Templates:**
- `cps/templates/ai_chat_panel.html` — the floating chat panel HTML (included by reader templates)
- `cps/templates/ai_admin.html` — AI provider/model config page (extends `layout.html`)

**Static assets:**
- `cps/static/js/ai_chat.js` — chat panel logic (send, stream render, history, markdown)
- `cps/static/js/ai_page_extract.js` — detect reader format (epub/pdf/txt) and extract current page text
- `cps/static/css/ai_chat.css` — chat panel styles (floating button + right drawer)

**Tests:**
- `tests/conftest.py` — pytest fixtures (Flask app, temp DB, logged-in client)
- `tests/test_provider_deepseek.py` — DeepSeek provider unit tests (mocked HTTP)
- `tests/test_ai_memory.py` — memory extraction/retrieval tests
- `tests/test_ai_routes.py` — chat API endpoint tests
- `tests/test_ai_models.py` — DB model tests

### Modified files (minimal intrusion — 6 files, ~8 lines total)

- `cps/main.py` — register `aichat` blueprint + call `register_authentik(app)` (3 lines added)
- `cps/templates/read.html` — `{% include 'ai_chat_panel.html' %}` (1 line)
- `cps/templates/readpdf.html` — `{% include 'ai_chat_panel.html' %}` (1 line)
- `cps/templates/readtxt.html` — `{% include 'ai_chat_panel.html' %}` (1 line)
- `cps/templates/layout.html` — add "AI Settings" link in admin nav (1 line, conditional on admin role)
- `pyproject.toml` — add `[tool.pytest.ini_options]` + pytest in optional dev deps

---

## Task 0: Test infrastructure setup

**Files:**
- Modify: `pyproject.toml` (add pytest config + dev dep)
- Create: `tests/conftest.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Add pytest config and dev dependency to pyproject.toml**

Read `/workspace/pyproject.toml` first to find the insertion point (after the `[project.optional-dependencies]` section or at end of file). Add:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

And in `[project.optional-dependencies]`, add a new `dev` key (if not present):

```toml
dev = [
    "pytest>=7.0,<9.0",
    "pytest-mock>=3.10,<4.0",
]
```

- [ ] **Step 2: Create tests/__init__.py (empty) and tests/conftest.py**

`tests/__init__.py`:
```python
```

`tests/conftest.py`:
```python
"""Shared pytest fixtures for the AI reading companion."""
import os
import sys
import tempfile
import pytest

# Ensure the workspace root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return a path to a fresh sqlite DB file for app metadata."""
    return str(tmp_path / "app.db")


@pytest.fixture
def app(tmp_db_path, monkeypatch):
    """Create a minimal calibre-web Flask app with a temp DB for testing."""
    # Point calibre-web's settings path at a temp file before import
    monkeypatch.setenv("CALIBREWEB_SETTINGS", tmp_db_path)
    from cps import create_app, ub
    # Force a fresh in-memory-ish app DB
    ub.app_DB_path = tmp_db_path
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    yield app


@pytest.fixture
def client(app):
    """Unauthenticated test client."""
    return app.test_client()


@pytest.fixture
def admin_client(app):
    """Test client logged in as the default admin user (password: admin123)."""
    client = app.test_client()
    rv = client.post("/login", data={"name": "admin", "password": "admin123"},
                     follow_redirects=True)
    assert rv.status_code == 200
    return client
```

- [ ] **Step 3: Install dev deps and verify pytest collects (0 tests is fine)**

Run: `pip install -e ".[dev]" && pytest --co -q`
Expected: `no tests ran` or `0 tests collected` with no errors.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml tests/__init__.py tests/conftest.py
git commit -m "test: add pytest infrastructure for AI companion feature"
```

---

## Task 1: AI crypto helpers

**Files:**
- Create: `cps/ai/__init__.py` (minimal, will grow in Task 6)
- Create: `cps/ai/crypto.py`
- Test: `tests/test_ai_crypto.py`

- [ ] **Step 1: Write the failing test**

`tests/test_ai_crypto.py`:
```python
"""Tests for AI config value encryption helpers."""
from cps.ai.crypto import encrypt_value, decrypt_value


class TestCrypto:
    def test_roundtrip_string(self):
        key = b"0123456789abcdef0123456789abcdef"  # 32-byte Fernet key
        original = "sk-deepseek-abc123"
        encrypted = encrypt_value(original, key)
        assert encrypted != original
        assert decrypt_value(encrypted, key) == original

    def test_decrypt_invalid_returns_empty(self):
        key = b"0123456789abcdef0123456789abcdef"
        assert decrypt_value("not-a-valid-token", key) == ""

    def test_encrypt_empty_returns_empty(self):
        key = b"0123456789abcdef0123456789abcdef"
        assert encrypt_value("", key) == ""
        assert encrypt_value(None, key) == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ai_crypto.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cps.ai'`

- [ ] **Step 3: Create cps/ai/__init__.py and cps/ai/crypto.py**

`cps/ai/__init__.py` (minimal stub for now — will be expanded in Task 6):
```python
"""AI reading companion subpackage for calibre-web.

All AI-related code (providers, chat API, memory, authentik OAuth) lives here
to minimize intrusion into upstream calibre-web.
"""
```

`cps/ai/crypto.py`:
```python
"""Encryption helpers for storing sensitive AI config values (API keys) at rest.

Uses Fernet symmetric encryption from the `cryptography` package, which is
already a calibre-web dependency. The encryption key is the same one calibre-web
generates for its own config secrets (see cps.config_sql.get_encryption_key).
"""
from cryptography.fernet import Fernet, InvalidToken


def encrypt_value(value, key):
    """Encrypt a string with the given 32-byte url-safe base64 Fernet key.

    Returns an empty string if value is falsy (no point encrypting empty).
    """
    if not value:
        return ""
    try:
        f = Fernet(key)
        return f.encrypt(value.encode("utf-8")).decode("utf-8")
    except Exception:
        # If encryption fails, return empty rather than crashing the app
        return ""


def decrypt_value(token, key):
    """Decrypt a Fernet token back to the original string.

    Returns empty string if the token is invalid or decryption fails.
    """
    if not token or not key:
        return ""
    try:
        f = Fernet(key)
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        return ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ai_crypto.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add cps/ai/__init__.py cps/ai/crypto.py tests/test_ai_crypto.py
git commit -m "feat(ai): add Fernet-based crypto helpers for API key storage"
```

---

## Task 2: AI database models

**Files:**
- Create: `cps/ai/models.py`
- Test: `tests/test_ai_models.py`

- [ ] **Step 1: Write the failing test**

`tests/test_ai_models.py`:
```python
"""Tests for AI SQLAlchemy models."""
from datetime import datetime, timezone

from cps.ai.models import (
    AiConfig, AiProvider, AiConversation, AiMessage, AiUserMemory,
)


class TestAiModels:
    def test_ai_config_defaults(self, app):
        from cps.ub import session, Base
        from sqlalchemy import create_engine
        # Models are registered on ub.Base; create_all on a fresh engine makes tables
        cfg = AiConfig()
        assert cfg.enabled is False
        assert cfg.default_provider == "deepseek"
        assert cfg.default_model == "deepseek-chat"
        assert cfg.memory_enabled is True

    def test_ai_provider_columns(self):
        p = AiProvider()
        p.provider_name = "deepseek"
        p.api_base = "https://api.deepseek.com"
        p.api_key_encrypted = "enc-token"
        p.models_json = '[{"id":"deepseek-chat","label":"DeepSeek Chat"}]'
        p.active = True
        assert p.provider_name == "deepseek"
        assert p.active is True

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

    def test_ai_user_memory(self):
        m = AiUserMemory()
        m.user_id = 1
        m.content = "User prefers concise explanations"
        m.source_book_id = 42
        assert m.user_id == 1
        assert m.source_book_id == 42
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ai_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'AiConfig'`

- [ ] **Step 3: Create cps/ai/models.py**

`cps/ai/models.py`:
```python
"""SQLAlchemy models for AI reading companion data.

All models inherit from calibre-web's `ub.Base` so they are auto-created by
`Base.metadata.create_all(engine)` on startup (see cps/ub.py:init_db). No
manual migration is needed — adding a new column requires bumping the schema
version check, but adding new tables is automatic.

Tables:
  ai_config        — singleton row of global AI settings (enabled, defaults)
  ai_provider      — per-provider config (api_base, encrypted api_key, models JSON)
  ai_conversation  — one per (user, book) chat thread
  ai_message       — individual messages in a conversation
  ai_user_memory   — cross-book long-term memory entries extracted from conversations
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from cps.ub import Base


class AiConfig(Base):
    __tablename__ = "ai_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    default_provider = Column(String, default="deepseek")
    default_model = Column(String, default="deepseek-chat")
    memory_enabled = Column(Boolean, default=True)
    memory_extract_interval = Column(Integer, default=10)  # extract after every N messages
    system_prompt_extra = Column(Text, default="")


class AiProvider(Base):
    __tablename__ = "ai_provider"

    id = Column(Integer, primary_key=True)
    provider_name = Column(String, unique=True)
    display_name = Column(String, default="")
    api_base = Column(String, default="")
    api_key_encrypted = Column(String, default="")
    models_json = Column(Text, default="[]")  # JSON array of {"id","label"}
    active = Column(Boolean, default=False)


class AiConversation(Base):
    __tablename__ = "ai_conversation"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    book_id = Column(Integer)
    book_format = Column(String, default="")
    title = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    messages = relationship("AiMessage", backref="conversation",
                            cascade="all, delete-orphan", lazy="dynamic")


class AiMessage(Base):
    __tablename__ = "ai_message"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversation.id"))
    role = Column(String)  # "user" | "assistant" | "system"
    content = Column(Text)
    page_context = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AiUserMemory(Base):
    __tablename__ = "ai_user_memory"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    content = Column(Text)
    source_book_id = Column(Integer, default=None)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ai_models.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add cps/ai/models.py tests/test_ai_models.py
git commit -m "feat(ai): add SQLAlchemy models for config, providers, conversations, memory"
```

---

## Task 3: Provider abstraction (base + DeepSeek)

**Files:**
- Create: `cps/ai/base.py`
- Create: `cps/ai/deepseek.py`
- Test: `tests/test_provider_deepseek.py`

- [ ] **Step 1: Write the failing test**

`tests/test_provider_deepseek.py`:
```python
"""Tests for the DeepSeek provider (HTTP mocked)."""
import json
from unittest.mock import patch, MagicMock

import pytest

from cps.ai.base import ModelInfo
from cps.ai.deepseek import DeepSeekProvider


class TestDeepSeekProvider:
    def test_provider_name(self):
        p = DeepSeekProvider(api_base="https://api.deepseek.com", api_key="sk-test")
        assert p.name == "deepseek"

    def test_available_models(self):
        p = DeepSeekProvider(api_base="https://api.deepseek.com", api_key="sk-test")
        models = p.available_models()
        ids = [m.id for m in models]
        assert "deepseek-chat" in ids

    def test_chat_stream_yields_deltas(self):
        """The chat() generator should yield content deltas from SSE response."""
        p = DeepSeekProvider(api_base="https://api.deepseek.com", api_key="sk-test")

        # Build a fake SSE response with two content chunks then [DONE]
        sse_lines = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":" world"}}]}\n\n',
            b'data: [DONE]\n\n',
        ]
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.iter_lines = MagicMock(return_value=iter(sse_lines))
        fake_response.__enter__ = MagicMock(return_value=fake_response)
        fake_response.__exit__ = MagicMock(return_value=False)

        with patch("cps.ai.deepseek.requests.post", return_value=fake_response) as mock_post:
            messages = [{"role": "user", "content": "hi"}]
            chunks = list(p.chat(messages, model="deepseek-chat"))

        assert chunks == ["Hello", " world"]
        # Verify the API was called with the OpenAI-compatible endpoint
        call_args = mock_post.call_args
        assert "/chat/completions" in call_args[1]["url"]
        assert call_args[1]["headers"]["Authorization"] == "Bearer sk-test"
        body = call_args[1]["json"]
        assert body["model"] == "deepseek-chat"
        assert body["stream"] is True

    def test_chat_non_stream_returns_full(self):
        """Non-streaming chat returns the full content string."""
        p = DeepSeekProvider(api_base="https://api.deepseek.com", api_key="sk-test")
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json = MagicMock(return_value={
            "choices": [{"message": {"content": "Full reply"}}]
        })
        with patch("cps.ai.deepseek.requests.post", return_value=fake_response):
            result = p.chat([{"role": "user", "content": "hi"}],
                            model="deepseek-chat", stream=False)
        assert result == "Full reply"

    def test_chat_raises_on_http_error(self):
        p = DeepSeekProvider(api_base="https://api.deepseek.com", api_key="sk-test")
        fake_response = MagicMock()
        fake_response.status_code = 401
        fake_response.text = "Unauthorized"
        with patch("cps.ai.deepseek.requests.post", return_value=fake_response):
            with pytest.raises(RuntimeError, match="DeepSeek API error 401"):
                list(p.chat([{"role": "user", "content": "hi"}], model="deepseek-chat"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_provider_deepseek.py -v`
Expected: FAIL with `ImportError: cannot import name 'ModelInfo'`

- [ ] **Step 3: Create cps/ai/base.py**

`cps/ai/base.py`:
```python
"""Abstract base for AI providers and the ModelInfo dataclass.

A provider implements `chat()` which returns either a streaming generator
(yielding string deltas) or a full string when stream=False. Providers are
registered in cps.ai.registry and instantiated from cps/ai/models.py AiProvider
rows.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, List, Dict, Union


@dataclass
class ModelInfo:
    """Metadata about a single model offered by a provider."""
    id: str
    label: str = ""
    context_window: int = 0  # 0 = unknown
    supports_streaming: bool = True


class BaseProvider(ABC):
    """Abstract AI provider. Subclasses implement the chat() call."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short provider identifier, e.g. 'deepseek'."""

    @abstractmethod
    def available_models(self) -> List[ModelInfo]:
        """Return the list of models this provider offers."""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], model: str,
             stream: bool = True, **kwargs) -> Union[Generator[str, None, None], str]:
        """Send a chat completion request.

        Args:
            messages: OpenAI-format message list [{"role","content"}, ...]
            model: model id to use
            stream: if True, return a generator yielding content deltas;
                    if False, return the full response string
            **kwargs: passed through to the underlying API (e.g. temperature)

        Raises:
            RuntimeError: on HTTP errors or malformed responses.
        """
```

- [ ] **Step 4: Create cps/ai/deepseek.py**

`cps/ai/deepseek.py`:
```python
"""DeepSeek provider — calls the OpenAI-compatible /chat/completions endpoint.

DeepSeek's API (https://api.deepseek.com) is OpenAI-compatible, so we use the
standard /v1/chat/completions path with `stream: true` for SSE streaming.

The provider is configured at runtime from an AiProvider DB row (api_base +
decrypted api_key). It supports both streaming (generator) and non-streaming
(full string) modes.
"""
import json
from typing import Dict, Generator, List, Union

import requests

from .base import BaseProvider, ModelInfo


class DeepSeekProvider(BaseProvider):
    """OpenAI-compatible chat completions provider for DeepSeek."""

    def __init__(self, api_base: str, api_key: str, timeout: int = 120):
        self._api_base = api_base.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "deepseek"

    def available_models(self) -> List[ModelInfo]:
        """Return the known DeepSeek models.

        These are hardcoded because DeepSeek's /models endpoint may list
        internal names. The admin can add custom model ids via the config UI.
        """
        return [
            ModelInfo(id="deepseek-chat", label="DeepSeek Chat (V3)",
                      context_window=64000, supports_streaming=True),
            ModelInfo(id="deepseek-reasoner", label="DeepSeek Reasoner (R1)",
                      context_window=64000, supports_streaming=True),
        ]

    def chat(self, messages: List[Dict[str, str]], model: str,
             stream: bool = True, **kwargs) -> Union[Generator[str, None, None], str]:
        url = f"{self._api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        payload.update(kwargs)

        if stream:
            return self._stream_chat(url, headers, payload)
        return self._blocking_chat(url, headers, payload)

    def _stream_chat(self, url, headers, payload) -> Generator[str, None, None]:
        with requests.post(url, headers=headers, json=payload,
                           stream=True, timeout=self._timeout) as resp:
            if resp.status_code != 200:
                raise RuntimeError(
                    f"DeepSeek API error {resp.status_code}: {resp.text}"
                )
            for line in resp.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8", errors="replace")
                if not line_str.startswith("data:"):
                    continue
                data = line_str[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {}).get("content", "")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    def _blocking_chat(self, url, headers, payload) -> str:
        resp = requests.post(url, headers=headers, json=payload,
                             timeout=self._timeout)
        if resp.status_code != 200:
            raise RuntimeError(
                f"DeepSeek API error {resp.status_code}: {resp.text}"
            )
        data = resp.json()
        return data["choices"][0]["message"]["content"]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_provider_deepseek.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add cps/ai/base.py cps/ai/deepseek.py tests/test_provider_deepseek.py
git commit -m "feat(ai): add provider base class and DeepSeek provider with SSE streaming"
```

---

## Task 4: Provider registry and config seeding

**Files:**
- Create: `cps/ai/registry.py`
- Modify: `cps/ai/__init__.py` (expand from Task 1 stub)
- Test: `tests/test_registry.py`

- [ ] **Step 1: Write the failing test**

`tests/test_registry.py`:
```python
"""Tests for the provider registry."""
import pytest

from cps.ai.registry import get_provider, register_provider_class, list_providers
from cps.ai.deepseek import DeepSeekProvider


class TestRegistry:
    def test_list_providers_includes_deepseek(self):
        names = list_providers()
        assert "deepseek" in names

    def test_get_provider_by_name(self):
        p = get_provider("deepseek", api_base="https://api.deepseek.com",
                         api_key="sk-test")
        assert isinstance(p, DeepSeekProvider)
        assert p.name == "deepseek"

    def test_get_unknown_provider_raises(self):
        with pytest.raises(KeyError, match="unknown"):
            get_provider("nonexistent", api_base="", api_key="")

    def test_register_custom_provider(self):
        from cps.ai.base import BaseProvider, ModelInfo

        class FakeProvider(BaseProvider):
            @property
            def name(self):
                return "fake"
            def available_models(self):
                return [ModelInfo(id="fake-1")]
            def chat(self, messages, model, stream=True, **kwargs):
                yield "fake reply"

        register_provider_class("fake", FakeProvider)
        assert "fake" in list_providers()
        p = get_provider("fake", api_base="", api_key="")
        assert isinstance(p, FakeProvider)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_registry.py -v`
Expected: FAIL with `ImportError: cannot import name 'get_provider'`

- [ ] **Step 3: Create cps/ai/registry.py**

`cps/ai/registry.py`:
```python
"""Provider registry — maps provider names to provider classes.

The registry holds the *classes* (not instances) so callers can instantiate
with runtime config (api_base, api_key) read from the AiProvider DB row.
"""
from typing import Dict, List, Type

from .base import BaseProvider
from .deepseek import DeepSeekProvider


_PROVIDER_CLASSES: Dict[str, Type[BaseProvider]] = {}


def register_provider_class(name: str, cls: Type[BaseProvider]) -> None:
    """Register a provider class under the given name."""
    _PROVIDER_CLASSES[name] = cls


def list_providers() -> List[str]:
    """Return the names of all registered provider classes."""
    return list(_PROVIDER_CLASSES.keys())


def get_provider(name: str, api_base: str, api_key: str,
                 **kwargs) -> BaseProvider:
    """Instantiate a provider by name with the given config.

    Raises KeyError if the name is not registered.
    """
    try:
        cls = _PROVIDER_CLASSES[name]
    except KeyError:
        raise KeyError(f"unknown provider: {name}")
    return cls(api_base=api_base, api_key=api_key, **kwargs)


# Register built-in providers at import time
register_provider_class("deepseek", DeepSeekProvider)
```

- [ ] **Step 4: Expand cps/ai/__init__.py to seed default config**

`cps/ai/__init__.py`:
```python
"""AI reading companion subpackage for calibre-web.

All AI-related code (providers, chat API, memory, authentik OAuth) lives here
to minimize intrusion into upstream calibre-web.

On first import, `seed_default_config()` ensures the AiConfig and AiProvider
tables have their default rows (deepseek provider, disabled by default).
"""
import logging

from cps.ub import session as ub_session

from . import registry  # noqa: F401 — registers built-in providers on import
from .models import AiConfig, AiProvider

log = logging.getLogger("cps.ai")


def seed_default_config():
    """Ensure the ai_config singleton and default providers exist in the DB.

    Safe to call multiple times — it only inserts missing rows.
    """
    try:
        cfg = ub_session.query(AiConfig).first()
        if cfg is None:
            cfg = AiConfig()
            ub_session.add(cfg)

        # Ensure the deepseek provider row exists
        dsp = ub_session.query(AiProvider).filter_by(provider_name="deepseek").first()
        if dsp is None:
            import json
            dsp = AiProvider()
            dsp.provider_name = "deepseek"
            dsp.display_name = "DeepSeek"
            dsp.api_base = "https://api.deepseek.com"
            dsp.api_key_encrypted = ""
            dsp.models_json = json.dumps([
                {"id": "deepseek-chat", "label": "DeepSeek Chat (V3)"},
                {"id": "deepseek-reasoner", "label": "DeepSeek Reasoner (R1)"},
            ])
            dsp.active = True
            ub_session.add(dsp)

        ub_session.commit()
    except Exception as e:
        log.warning("seed_default_config failed: %s", e)
        ub_session.rollback()


# Seed on import (the ub.session is initialized before this import in create_app)
try:
    seed_default_config()
except Exception:
    pass
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_registry.py tests/test_ai_crypto.py tests/test_ai_models.py tests/test_provider_deepseek.py -v`
Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add cps/ai/registry.py cps/ai/__init__.py tests/test_registry.py
git commit -m "feat(ai): add provider registry and default config seeding"
```

---

## Task 5: Memory system (extraction + retrieval)

**Files:**
- Create: `cps/ai/memory.py`
- Test: `tests/test_ai_memory.py`

- [ ] **Step 1: Write the failing test**

`tests/test_ai_memory.py`:
```python
"""Tests for the AI memory system."""
from unittest.mock import patch, MagicMock

import pytest

from cps.ai.memory import (
    build_system_prompt, extract_user_memory, get_user_memory_strings,
    should_extract_memory,
)


class TestMemory:
    def test_build_system_prompt_includes_metadata(self):
        prompt = build_system_prompt(
            book_title="Dune",
            book_authors=["Frank Herbert"],
            book_description="A sci-fi epic about desert planet Arrakis.",
            book_tags=["sci-fi", "classic"],
            page_context="Chapter 1: the spice must flow...",
            user_memory=["User prefers brief answers"],
            extra_prompt="",
        )
        assert "Dune" in prompt
        assert "Frank Herbert" in prompt
        assert "sci-fi" in prompt
        assert "Chapter 1" in prompt
        assert "brief answers" in prompt

    def test_should_extract_memory(self):
        # Extract every 10 messages by default
        assert should_extract_memory(message_count=10) is True
        assert should_extract_memory(message_count=9, interval=10) is False
        assert should_extract_memory(message_count=20, interval=10) is True
        assert should_extract_memory(message_count=15, interval=10) is False

    def test_extract_user_memory_calls_ai(self):
        """extract_user_memory should call the provider and return a memory string."""
        fake_provider = MagicMock()
        fake_provider.chat.return_value = "User enjoys epic worldbuilding"

        result = extract_user_memory(
            provider=fake_provider,
            model="deepseek-chat",
            recent_messages=[
                {"role": "user", "content": "Tell me about Arrakis"},
                {"role": "assistant", "content": "Arrakis is a desert planet..."},
            ],
            user_id=1,
            book_id=42,
        )

        assert result == "User enjoys epic worldbuilding"
        # Verify the provider was called with a prompt asking to extract insights
        call_messages = fake_provider.chat.call_args[0][0]
        assert "extract" in call_messages[0]["content"].lower() or "insight" in call_messages[0]["content"].lower()

    def test_get_user_memory_strings(self, app):
        from cps.ub import session
        from cps.ai.models import AiUserMemory
        # Clean slate
        session.query(AiUserMemory).delete()
        session.commit()
        m1 = AiUserMemory(user_id=1, content="Likes sci-fi", source_book_id=1)
        m2 = AiUserMemory(user_id=1, content="Prefers concise answers", source_book_id=2)
        session.add_all([m1, m2])
        session.commit()

        mems = get_user_memory_strings(user_id=1, limit=10)
        assert "Likes sci-fi" in mems
        assert "Prefers concise answers" in mems
        assert len(mems) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ai_memory.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_system_prompt'`

- [ ] **Step 3: Create cps/ai/memory.py**

`cps/ai/memory.py`:
```python
"""AI memory system: system-prompt construction + cross-book memory extraction.

Two responsibilities:
1. `build_system_prompt()` — assembles the system prompt sent to the LLM from
   book metadata, current page text, and the user's long-term memories.
2. `extract_user_memory()` — calls the LLM with recent conversation messages
   and asks it to produce a concise insight about the user; the result is
   stored in AiUserMemory for injection into future conversations.
"""
import json
from datetime import datetime, timezone
from typing import List, Optional

from cps.ub import session as ub_session
from cps import logger

from .models import AiUserMemory

log = logger.create()


def build_system_prompt(book_title: str,
                        book_authors: List[str],
                        book_description: str,
                        book_tags: List[str],
                        page_context: str,
                        user_memory: List[str],
                        extra_prompt: str = "") -> str:
    """Build the system prompt for an AI chat about a book.

    The prompt instructs the AI to act as a reading companion, gives it the
    book's metadata and the current page text, and injects any long-term
    user memories so the AI has continuity across books.
    """
    authors_str = ", ".join(book_authors) if book_authors else "Unknown"
    tags_str = ", ".join(book_tags) if book_tags else ""
    memory_str = "\n".join(f"- {m}" for m in user_memory) if user_memory else "(none yet)"

    # Truncate page context to avoid blowing the context window
    max_page_chars = 8000
    if len(page_context) > max_page_chars:
        page_context = page_context[:max_page_chars] + "\n...[truncated]"

    parts = [
        "You are an AI reading companion helping the user understand a book they are currently reading.",
        "Answer questions, explain passages, and discuss themes based on the book's metadata and the current page text provided below.",
        "Be concise and helpful. If the user's question is unrelated to the book, gently redirect.",
        "",
        f"## Book Metadata",
        f"Title: {book_title}",
        f"Author(s): {authors_str}",
    ]
    if tags_str:
        parts.append(f"Tags: {tags_str}")
    if book_description:
        # Strip HTML from description (calibre stores it as HTML)
        import re
        desc = re.sub(r"<[^>]+>", "", book_description).strip()
        if len(desc) > 1000:
            desc = desc[:1000] + "..."
        parts.append(f"Description: {desc}")
    parts.extend([
        "",
        f"## Current Page Text",
        page_context if page_context else "(no page context provided)",
        "",
        f"## What you remember about this user (long-term memory)",
        memory_str,
    ])
    if extra_prompt:
        parts.extend(["", f"## Additional instructions\n{extra_prompt}"])
    return "\n".join(parts)


def should_extract_memory(message_count: int, interval: int = 10) -> bool:
    """Return True if memory extraction should run after this many messages."""
    if interval <= 0:
        return False
    return message_count > 0 and message_count % interval == 0


def extract_user_memory(provider, model: str, recent_messages: list,
                        user_id: int, book_id: int) -> Optional[str]:
    """Call the provider to extract a concise user-memory insight from recent messages.

    Stores the result in AiUserMemory and returns the extracted string (or None).
    """
    extraction_prompt = (
        "You are a memory assistant. Read the following conversation between a user and an AI reading companion. "
        "Extract ONE concise sentence capturing a durable insight about this user — their reading preferences, "
        "interests, knowledge level, or what they care about. "
        "Output only the sentence, no preamble. If there is nothing worth remembering, output exactly: NONE"
    )
    messages = [{"role": "system", "content": extraction_prompt}]
    # Include up to the last 12 messages of context
    for m in recent_messages[-12:]:
        messages.append({"role": m["role"], "content": m["content"]})

    try:
        result = provider.chat(messages, model=model, stream=False)
        result = (result or "").strip()
    except Exception as e:
        log.warning("memory extraction failed: %s", e)
        return None

    if not result or result.upper() == "NONE":
        return None

    try:
        mem = AiUserMemory()
        mem.user_id = user_id
        mem.content = result
        mem.source_book_id = book_id
        ub_session.add(mem)
        ub_session.commit()
    except Exception as e:
        log.warning("failed to store user memory: %s", e)
        ub_session.rollback()

    return result


def get_user_memory_strings(user_id: int, limit: int = 20) -> List[str]:
    """Return the user's long-term memory entries as a list of strings (newest first)."""
    try:
        mems = ub_session.query(AiUserMemory).filter_by(user_id=user_id)\
            .order_by(AiUserMemory.created_at.desc()).limit(limit).all()
        return [m.content for m in mems]
    except Exception as e:
        log.warning("failed to load user memory: %s", e)
        return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ai_memory.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add cps/ai/memory.py tests/test_ai_memory.py
git commit -m "feat(ai): add memory system with system-prompt builder and cross-book extraction"
```

---

## Task 6: Chat API routes (streaming + history)

**Files:**
- Create: `cps/ai/routes.py`
- Test: `tests/test_ai_routes.py`

- [ ] **Step 1: Write the failing test**

`tests/test_ai_routes.py`:
```python
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

    def test_chat_streams_response(self, admin_client, app):
        """POST /ai/chat should stream SSE chunks back."""
        from cps.ai.models import AiConfig, AiProvider
        from cps.ub import session
        from cps.ai.crypto import encrypt_value
        # Enable AI and set a fake api key
        cfg = session.query(AiConfig).first()
        cfg.enabled = True
        dsp = session.query(AiProvider).filter_by(provider_name="deepseek").first()
        # Use a known 32-byte key for the test app
        key = b"0123456789abcdef0123456789abcdef"
        dsp.api_key_encrypted = encrypt_value("sk-test", key)
        session.commit()

        fake_provider = MagicMock()
        fake_provider.chat.return_value = iter(["Hello ", "world"])

        with patch("cps.ai.routes.get_active_provider", return_value=fake_provider):
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

    def test_clear_history(self, admin_client):
        rv = admin_client.delete("/ai/history/1")
        assert rv.status_code == 200

    def test_admin_page_get(self, admin_client):
        rv = admin_client.get("/ai/admin")
        assert rv.status_code == 200
        assert b"DeepSeek" in rv.data or b"deepseek" in rv.data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ai_routes.py -v`
Expected: FAIL with 404 (routes not registered yet)

- [ ] **Step 3: Create cps/ai/routes.py**

`cps/ai/routes.py`:
```python
"""AI companion blueprint — chat API, history, memory, and admin config routes.

All routes are mounted under /ai/. The blueprint is registered in cps/main.py.
Authentication uses calibre-web's existing `user_login_required` decorator.
CSRF is handled automatically by Flask-WTF's CSRFProtect (the frontend sends
the X-CSRFToken header via jQuery ajaxSetup in main.js, or the token in form data).
"""
import json
from flask import Blueprint, Response, request, jsonify, stream_with_context, abort
from flask_babel import gettext as _

from cps import logger, calibre_db, ub, config, app
from cps.cw_login import current_user
from cps.usermanagement import user_login_required

from .models import (AiConfig, AiProvider, AiConversation, AiMessage, AiUserMemory)
from .registry import get_provider, list_providers
from .crypto import encrypt_value, decrypt_value
from .memory import (build_system_prompt, extract_user_memory,
                     get_user_memory_strings, should_extract_memory)

log = logger.create()

aichat = Blueprint("aichat", __name__)


def _get_encryption_key():
    """Get the Fernet key calibre-web uses for config secrets."""
    from cps import config_sql
    import os
    settings_path = os.path.dirname(ub.app_DB_path)
    key, _ = config_sql.get_encryption_key(settings_path)
    return key


def get_active_provider():
    """Instantiate the active provider from DB config.

    Returns (provider_instance, model_id) or raises RuntimeError if AI is
    disabled or no provider is configured.
    """
    from cps.ub import session as ub_session
    cfg = ub_session.query(AiConfig).first()
    if cfg is None or not cfg.enabled:
        raise RuntimeError("AI companion is disabled")

    provider_name = cfg.default_provider
    prov_row = ub_session.query(AiProvider).filter_by(provider_name=provider_name).first()
    if prov_row is None:
        raise RuntimeError(f"provider '{provider_name}' not configured")

    key = _get_encryption_key()
    api_key = decrypt_value(prov_row.api_key_encrypted, key)
    if not api_key:
        raise RuntimeError(f"provider '{provider_name}' has no API key set")

    provider = get_provider(provider_name, api_base=prov_row.api_base, api_key=api_key)
    return provider, cfg.default_model


def _serialize_message(msg):
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "page_context": msg.page_context or "",
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def _get_or_create_conversation(user_id, book_id, book_format, title):
    from cps.ub import session as ub_session
    conv = ub_session.query(AiConversation).filter_by(
        user_id=user_id, book_id=book_id
    ).first()
    if conv is None:
        conv = AiConversation()
        conv.user_id = user_id
        conv.book_id = book_id
        conv.book_format = book_format or ""
        conv.title = title or ""
        ub_session.add(conv)
        ub_session.commit()
    return conv


@aichat.route("/ai/chat", methods=["POST"])
@user_login_required
def chat():
    """Stream a chat completion response.

    Request JSON: {book_id, book_format, message, page_context, book_title?,
                   book_authors?, book_description?, book_tags?}
    Response: text/event-stream of content deltas (data: <chunk>\\n\\n),
    terminated by data: [DONE].
    """
    data = request.get_json(silent=True) or {}
    book_id = data.get("book_id")
    message = data.get("message", "").strip()
    if not book_id or not message:
        return jsonify({"error": "book_id and message are required"}), 400

    # Try to fetch book metadata from calibre DB if not provided by frontend
    book_title = data.get("book_title", "")
    book_authors = data.get("book_authors", [])
    book_description = data.get("book_description", "")
    book_tags = data.get("book_tags", [])

    try:
        book = calibre_db.get_filtered_book(book_id)
        if book:
            if not book_title:
                book_title = book.title
            if not book_authors:
                book_authors = [a.name for a in book.authors]
            if not book_description:
                if book.comments:
                    book_description = book.comments[0].text or ""
            if not book_tags:
                book_tags = [t.name for t in book.tags]
    except Exception as e:
        log.warning("could not fetch book metadata for %s: %s", book_id, e)

    page_context = data.get("page_context", "")
    book_format = data.get("book_format", "")

    # Load config + memory
    from cps.ub import session as ub_session
    cfg = ub_session.query(AiConfig).first()
    user_memory = []
    if cfg and cfg.memory_enabled:
        user_memory = get_user_memory_strings(current_user.id, limit=10)

    system_prompt = build_system_prompt(
        book_title=book_title or "Unknown",
        book_authors=book_authors,
        book_description=book_description,
        book_tags=book_tags,
        page_context=page_context,
        user_memory=user_memory,
        extra_prompt=cfg.system_prompt_extra if cfg else "",
    )

    # Get or create conversation + load history
    conv = _get_or_create_conversation(current_user.id, book_id, book_format, book_title)
    history_msgs = ub_session.query(AiMessage).filter_by(conversation_id=conv.id)\
        .order_by(AiMessage.created_at.asc()).all()

    messages = [{"role": "system", "content": system_prompt}]
    for hm in history_msgs:
        messages.append({"role": hm.role, "content": hm.content})
    messages.append({"role": "user", "content": message})

    # Save the user message
    user_msg = AiMessage()
    user_msg.conversation_id = conv.id
    user_msg.role = "user"
    user_msg.content = message
    user_msg.page_context = page_context[:4000]  # truncate stored context
    ub_session.add(user_msg)
    ub_session.commit()

    try:
        provider, model = get_active_provider()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503

    def generate():
        full_reply = []
        try:
            for delta in provider.chat(messages, model=model, stream=True):
                full_reply.append(delta)
                yield f"data: {json.dumps({'delta': delta})}\n\n"
        except Exception as e:
            log.error("chat streaming error: %s", e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
            return

        # Save the assistant reply
        reply_text = "".join(full_reply)
        try:
            asst_msg = AiMessage()
            asst_msg.conversation_id = conv.id
            asst_msg.role = "assistant"
            asst_msg.content = reply_text
            ub_session.add(asst_msg)
            ub_session.commit()

            # Maybe extract memory
            if cfg and cfg.memory_enabled:
                msg_count = ub_session.query(AiMessage).filter_by(
                    conversation_id=conv.id).count()
                if should_extract_memory(msg_count, cfg.memory_extract_interval):
                    all_msgs = [{"role": m.role, "content": m.content} for m in
                                ub_session.query(AiMessage).filter_by(
                                    conversation_id=conv.id).order_by(
                                    AiMessage.created_at.asc()).all()]
                    try:
                        extract_user_memory(provider, model, all_msgs,
                                            current_user.id, book_id)
                    except Exception as e:
                        log.warning("memory extraction failed: %s", e)
        except Exception as e:
            log.error("failed to save assistant message: %s", e)
            ub_session.rollback()

        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"})


@aichat.route("/ai/history/<int:book_id>", methods=["GET"])
@user_login_required
def history(book_id):
    """Return the conversation history for a book as JSON."""
    from cps.ub import session as ub_session
    conv = ub_session.query(AiConversation).filter_by(
        user_id=current_user.id, book_id=book_id).first()
    if conv is None:
        return jsonify({"messages": []})
    msgs = conv.messages.order_by(AiMessage.created_at.asc()).all()
    return jsonify({"messages": [_serialize_message(m) for m in msgs]})


@aichat.route("/ai/history/<int:book_id>", methods=["DELETE"])
@user_login_required
def clear_history(book_id):
    """Delete the conversation (and all its messages) for a book."""
    from cps.ub import session as ub_session
    conv = ub_session.query(AiConversation).filter_by(
        user_id=current_user.id, book_id=book_id).first()
    if conv:
        ub_session.delete(conv)
        ub_session.commit()
    return jsonify({"status": "ok"})


@aichat.route("/ai/memory", methods=["GET"])
@user_login_required
def get_memory():
    """Return the current user's long-term memory entries."""
    mems = get_user_memory_strings(current_user.id, limit=50)
    return jsonify({"memories": mems})


@aichat.route("/ai/memory/clear", methods=["POST"])
@user_login_required
def clear_memory():
    """Delete all long-term memory entries for the current user."""
    from cps.ub import session as ub_session
    ub_session.query(AiUserMemory).filter_by(user_id=current_user.id).delete()
    ub_session.commit()
    return jsonify({"status": "ok"})


@aichat.route("/ai/admin", methods=["GET", "POST"])
@user_login_required
def admin():
    """AI provider/model configuration page (admin only)."""
    if not current_user.role_admin():
        abort(403)
    from cps.ub import session as ub_session

    if request.method == "POST":
        cfg = ub_session.query(AiConfig).first()
        if cfg is None:
            cfg = AiConfig()
            ub_session.add(cfg)
        cfg.enabled = request.form.get("enabled") == "on"
        cfg.default_provider = request.form.get("default_provider", "deepseek")
        cfg.default_model = request.form.get("default_model", "deepseek-chat")
        cfg.memory_enabled = request.form.get("memory_enabled") == "on"
        try:
            cfg.memory_extract_interval = int(request.form.get("memory_extract_interval", 10))
        except ValueError:
            cfg.memory_extract_interval = 10
        cfg.system_prompt_extra = request.form.get("system_prompt_extra", "")

        # Update provider configs
        key = _get_encryption_key()
        for prov in ub_session.query(AiProvider).all():
            field_prefix = f"provider_{prov.id}_"
            prov.api_base = request.form.get(field_prefix + "api_base", prov.api_base)
            new_key = request.form.get(field_prefix + "api_key", "")
            if new_key:
                prov.api_key_encrypted = encrypt_value(new_key, key)
            prov.active = request.form.get(field_prefix + "active") == "on"
            models_text = request.form.get(field_prefix + "models", "")
            # Parse simple newline-separated "id|label" lines into JSON
            models_list = []
            for line in models_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                if "|" in line:
                    mid, mlabel = line.split("|", 1)
                else:
                    mid, mlabel = line, line
                models_list.append({"id": mid.strip(), "label": mlabel.strip()})
            prov.models_json = json.dumps(models_list)

        ub_session.commit()

    cfg = ub_session.query(AiConfig).first()
    if cfg is None:
        cfg = AiConfig()
        ub_session.add(cfg)
        ub_session.commit()
    providers = ub_session.query(AiProvider).all()
    available_provider_classes = list_providers()

    from cps.render_template import render_title_template
    return render_title_template("ai_admin.html", title=_("AI Companion Settings"),
                                 config=cfg, providers=providers,
                                 available_providers=available_provider_classes,
                                 page="aiadmin")
```

- [ ] **Step 4: Create the admin template cps/templates/ai_admin.html**

`cps/templates/ai_admin.html`:
```html
{% extends "layout.html" %}
{% block body %}
<div class="container-fluid">
  <div class="row">
    <div class="col-sm-10">
      <h2>{{_('AI Companion Settings')}}</h2>
      <form method="post" action="{{ url_for('aichat.admin') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

        <div class="form-group">
          <label><input type="checkbox" name="enabled" {% if config.enabled %}checked{% endif %}> {{_('Enable AI Companion')}}</label>
        </div>
        <div class="form-group">
          <label><input type="checkbox" name="memory_enabled" {% if config.memory_enabled %}checked{% endif %}> {{_('Enable long-term memory')}}</label>
        </div>
        <div class="form-group">
          <label>{{_('Default Provider')}}</label>
          <select name="default_provider" class="form-control">
            {% for p in available_providers %}
            <option value="{{ p }}" {% if config.default_provider == p %}selected{% endif %}>{{ p }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="form-group">
          <label>{{_('Default Model')}}</label>
          <input type="text" name="default_model" class="form-control" value="{{ config.default_model }}">
        </div>
        <div class="form-group">
          <label>{{_('Extract memory every N messages')}}</label>
          <input type="number" name="memory_extract_interval" class="form-control" value="{{ config.memory_extract_interval }}" min="1" max="100">
        </div>
        <div class="form-group">
          <label>{{_('Extra system prompt instructions')}}</label>
          <textarea name="system_prompt_extra" class="form-control" rows="3">{{ config.system_prompt_extra }}</textarea>
        </div>

        <h3>{{_('Providers')}}</h3>
        {% for prov in providers %}
        <div class="panel panel-default">
          <div class="panel-heading">
            <h4>{{ prov.display_name or prov.provider_name }}
              <label class="pull-right"><input type="checkbox" name="provider_{{ prov.id }}_active" {% if prov.active %}checked{% endif %}> {{_('Active')}}</label>
            </h4>
          </div>
          <div class="panel-body">
            <div class="form-group">
              <label>{{_('API Base URL')}}</label>
              <input type="text" name="provider_{{ prov.id }}_api_base" class="form-control" value="{{ prov.api_base }}">
            </div>
            <div class="form-group">
              <label>{{_('API Key')}} {{_('(leave blank to keep current)')}}</label>
              <input type="password" name="provider_{{ prov.id }}_api_key" class="form-control" placeholder="sk-...">
            </div>
            <div class="form-group">
              <label>{{_('Models (one per line, format: id|label)')}}</label>
              <textarea name="provider_{{ prov.id }}_models" class="form-control" rows="3">{% set models = prov.models_json | from_json %}{% for m in models %}{{ m.id }}|{{ m.label }}
{% endfor %}</textarea>
            </div>
          </div>
        </div>
        {% endfor %}

        <button type="submit" class="btn btn-primary">{{_('Save')}}</button>
        <a href="{{ url_for('admin.admin') }}" class="btn btn-default">{{_('Back to Admin')}}</a>
      </form>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Register the from_json Jinja filter**

The template above uses `| from_json`. Add this filter to `cps/jinjia.py`. First read cps/jinjia.py to find where filters are registered.

Run: Read `/workspace/cps/jinjia.py` and find the filter registration block. Add a `from_json` filter:

```python
import json as _json
# ... inside the filter registration function:
@jinjia.app_template_filter('from_json')
def from_json(value):
    return _json.loads(value) if value else []
```

(Place this alongside the existing `@jinjia.app_template_filter` registrations — read the file to find the exact location and pattern.)

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_ai_routes.py -v`
Expected: 5 passed

- [ ] **Step 7: Commit**

```bash
git add cps/ai/routes.py cps/templates/ai_admin.html cps/jinjia.py tests/test_ai_routes.py
git commit -m "feat(ai): add chat streaming API, history, memory, and admin config routes"
```

---

## Task 7: Register the aichat blueprint in main.py

**Files:**
- Modify: `cps/main.py` (add 3 lines)

- [ ] **Step 1: Read the current main.py around the blueprint registration block**

Run: Read `/workspace/cps/main.py` lines 60-85 to confirm the insertion point (after `app.register_blueprint(editbook)` on line 78).

- [ ] **Step 2: Add the aichat blueprint registration**

In `/workspace/cps/main.py`, after line 78 (`app.register_blueprint(editbook)`), add:

```python
    from cps.ai.routes import aichat
    app.register_blueprint(aichat)
```

And after the oauth block (line 84), add the authentik registration call (will be wired in Task 9, but import it now guarded by a try/except):

```python
    try:
        from cps.ai.authentik import register_authentik
        register_authentik(app)
    except ImportError:
        pass
```

Also add `from cps import ai` near the top imports (after `from . import web_server` on line 62) to trigger the default-config seeding:

```python
    from cps import ai  # noqa: F401 — seeds default AI config on import
```

- [ ] **Step 3: Verify the app starts and the /ai/admin route is reachable**

Run: `python -c "from cps.main import main; main()" &; sleep 3; curl -s http://localhost:8083/ai/admin -o /dev/null -w "%{http_code}"; kill %1`
Expected: HTTP 302 (redirect to login) or 200 — not 404.

(If the dev server port differs, check cps/server.py defaults. The key assertion is no 404.)

- [ ] **Step 4: Commit**

```bash
git add cps/main.py
git commit -m "feat(ai): register aichat blueprint in main.py"
```

---

## Task 8: Frontend — chat panel JS/CSS and page extraction

**Files:**
- Create: `cps/static/css/ai_chat.css`
- Create: `cps/static/js/ai_page_extract.js`
- Create: `cps/static/js/ai_chat.js`
- Create: `cps/templates/ai_chat_panel.html`

- [ ] **Step 1: Create the chat panel CSS**

`cps/static/css/ai_chat.css`:
```css
/* AI Companion floating chat panel — injected into reader pages.
   Styles are scoped under #ai-companion-root to avoid clashing with reader CSS. */
#ai-companion-root { all: initial; }

#ai-companion-root * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }

#ai-companion-fab {
  position: fixed; bottom: 24px; right: 24px; z-index: 2147483646;
  width: 56px; height: 56px; border-radius: 50%;
  background: #4285f4; color: #fff; border: none; cursor: pointer;
  font-size: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.2s;
}
#ai-companion-fab:hover { transform: scale(1.08); }

#ai-companion-drawer {
  position: fixed; top: 0; right: 0; z-index: 2147483647;
  width: 420px; max-width: 100vw; height: 100vh;
  background: #fff; box-shadow: -4px 0 24px rgba(0,0,0,0.2);
  display: none; flex-direction: column;
}
#ai-companion-drawer.open { display: flex; }

#ai-companion-drawer header {
  padding: 12px 16px; background: #4285f4; color: #fff;
  display: flex; align-items: center; justify-content: space-between;
}
#ai-companion-drawer header h3 { margin: 0; font-size: 16px; font-weight: 600; }
#ai-companion-drawer header button { background: none; border: none; color: #fff; font-size: 20px; cursor: pointer; }

#ai-chat-messages { flex: 1; overflow-y: auto; padding: 16px; background: #f9f9f9; }
.ai-chat-msg { margin-bottom: 12px; padding: 10px 14px; border-radius: 12px; max-width: 88%; word-wrap: break-word; }
.ai-chat-msg.user { background: #4285f4; color: #fff; margin-left: auto; }
.ai-chat-msg.assistant { background: #fff; color: #333; border: 1px solid #e0e0e0; }
.ai-chat-msg.assistant pre { background: #f0f0f0; padding: 8px; border-radius: 4px; overflow-x: auto; }
.ai-chat-msg.assistant code { font-family: monospace; font-size: 13px; }

#ai-chat-input-area { padding: 12px; border-top: 1px solid #e0e0e0; background: #fff; }
#ai-chat-input { width: 100%; min-height: 60px; max-height: 120px; padding: 8px; border: 1px solid #ccc; border-radius: 8px; resize: none; font-size: 14px; }
#ai-chat-send { margin-top: 8px; padding: 8px 20px; background: #4285f4; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; }
#ai-chat-send:disabled { background: #aaa; cursor: not-allowed; }
.ai-chat-typing { color: #999; font-style: italic; }
```

- [ ] **Step 2: Create the page-extraction JS**

`cps/static/js/ai_page_extract.js`:
```javascript
/* Detects which reader is active (epub/pdf/txt) and extracts the current page text.
   Exposes window.AICompanion.getPageContext() -> string.
   This file is loaded by ai_chat_panel.html (included in each reader template). */
(function () {
  "use strict";
  window.AICompanion = window.AICompanion || {};

  function truncate(text, max) {
    max = max || 8000;
    if (!text) return "";
    text = text.replace(/\s+/g, " ").trim();
    return text.length > max ? text.slice(0, max) + "..." : text;
  }

  function extractEpub() {
    try {
      if (typeof reader === "undefined" || !reader || !reader.rendition) return "";
      var contents = reader.rendition.getContents();
      if (!contents || !contents.length) return "";
      // epub.js: each content is an iframe-like view; grab its document body text
      var texts = [];
      for (var i = 0; i < contents.length; i++) {
        var doc = contents[i].document || (contents[i].contentDocument || contents[i]);
        if (doc && doc.body) {
          texts.push(doc.body.innerText || doc.body.textContent || "");
        }
      }
      return truncate(texts.join("\n\n"));
    } catch (e) {
      console.warn("AICompanion epub extract failed:", e);
      return "";
    }
  }

  function extractPdf() {
    try {
      if (typeof PDFViewerApplication === "undefined" || !PDFViewerApplication.pdfDocument) return "";
      var pageNum = PDFViewerApplication.page || 1;
      // getTextContent is async; we return a placeholder and resolve via the async path
      return ""; // handled by async extractor below
    } catch (e) {
      return "";
    }
  }

  function extractTxt() {
    try {
      var el = document.getElementById("content");
      if (el) return truncate(el.innerText || el.textContent);
      return "";
    } catch (e) {
      return "";
    }
  }

  function detectFormat() {
    if (typeof reader !== "undefined" && reader && reader.rendition) return "epub";
    if (typeof PDFViewerApplication !== "undefined") return "pdf";
    if (document.getElementById("content") && document.getElementById("readmain")) return "txt";
    return "unknown";
  }

  // Synchronous extractor (best-effort)
  window.AICompanion.getPageContext = function () {
    var fmt = detectFormat();
    if (fmt === "epub") return extractEpub();
    if (fmt === "txt") return extractTxt();
    if (fmt === "pdf") return extractPdf();
    return "";
  };

  // Async extractor (for PDF which needs getTextContent)
  window.AICompanion.getPageContextAsync = function () {
    var fmt = detectFormat();
    if (fmt === "pdf" && typeof PDFViewerApplication !== "undefined" && PDFViewerApplication.pdfDocument) {
      var pageNum = PDFViewerApplication.page || 1;
      return PDFViewerApplication.pdfDocument.getPage(pageNum).then(function (page) {
        return page.getTextContent();
      }).then(function (tc) {
        var text = (tc.items || []).map(function (it) { return it.str; }).join(" ");
        return truncate(text);
      }).catch(function () { return ""; });
    }
    return Promise.resolve(window.AICompanion.getPageContext());
  };

  window.AICompanion.detectFormat = detectFormat;
})();
```

- [ ] **Step 3: Create the chat panel JS**

`cps/static/js/ai_chat.js`:
```javascript
/* AI Companion chat panel logic.
   - Loads conversation history for the current book on open
   - Sends messages via fetch (streaming SSE) and renders markdown
   - Includes current page context extracted by ai_page_extract.js
   Depends on: jQuery (loaded by reader pages), ai_page_extract.js, markdown2 (rendered server-side fallback uses marked if available) */
(function ($) {
  "use strict";
  if (!window.AICompanion) return;

  var BOOK_ID = null;
  var BOOK_FORMAT = null;
  var BOOK_META = null;
  var sending = false;

  function getCsrfToken() {
    return $("input[name='csrf_token']").val() || "";
  }

  function getBookIdFromUrl() {
    var m = window.location.pathname.match(/\/read\/(\d+)\/([A-Za-z0-9]+)/);
    if (m) return { id: parseInt(m[1], 10), format: m[2] };
    return { id: null, format: null };
  }

  function init() {
    var info = getBookIdFromUrl();
    BOOK_ID = info.id;
    BOOK_FORMAT = info.format;
    BOOK_META = window.AICompanionBookMeta || {};

    $("#ai-companion-fab").on("click", toggleDrawer);
    $("#ai-companion-close").on("click", closeDrawer);
    $("#ai-chat-send").on("click", sendMessage);
    $("#ai-chat-input").on("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    loadHistory();
  }

  function toggleDrawer() {
    $("#ai-companion-drawer").toggleClass("open");
  }
  function closeDrawer() {
    $("#ai-companion-drawer").removeClass("open");
  }

  function loadHistory() {
    if (!BOOK_ID) return;
    $.getJSON("/ai/history/" + BOOK_ID, function (data) {
      var $box = $("#ai-chat-messages").empty();
      (data.messages || []).forEach(function (m) {
        appendMessage(m.role, m.content);
      });
      scrollMessages();
    });
  }

  function appendMessage(role, content) {
    var safe = renderMarkdown(content);
    var cls = role === "user" ? "user" : "assistant";
    $('<div class="ai-chat-msg ' + cls + '"></div>').html(safe).appendTo("#ai-chat-messages");
    scrollMessages();
  }

  function renderMarkdown(text) {
    // Minimal markdown: code blocks, inline code, bold, line breaks.
    // (Server returns plain text; we do lightweight client-side rendering.)
    if (!text) return "";
    var esc = $("<div>").text(text).html(); // escape HTML first
    esc = esc.replace(/```([\s\S]*?)```/g, function (_, code) {
      return "<pre><code>" + code.replace(/^\n/, "") + "</code></pre>";
    });
    esc = esc.replace(/`([^`]+)`/g, "<code>$1</code>");
    esc = esc.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    esc = esc.replace(/\n/g, "<br>");
    return esc;
  }

  function scrollMessages() {
    var box = document.getElementById("ai-chat-messages");
    if (box) box.scrollTop = box.scrollHeight;
  }

  function sendMessage() {
    if (sending) return;
    var $input = $("#ai-chat-input");
    var text = $input.val().trim();
    if (!text || !BOOK_ID) return;

    appendMessage("user", text);
    $input.val("");

    // Get current page context (async for PDF)
    window.AICompanion.getPageContextAsync().then(function (pageCtx) {
      streamChat(text, pageCtx);
    });
  }

  function streamChat(message, pageContext) {
    sending = true;
    $("#ai-chat-send").prop("disabled", true);

    // Create a placeholder for the streaming response
    var $msg = $('<div class="ai-chat-msg assistant"><span class="ai-chat-typing">...</span></div>')
      .appendTo("#ai-chat-messages");
    scrollMessages();
    var fullText = "";

    fetch("/ai/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        book_id: BOOK_ID,
        book_format: BOOK_FORMAT,
        message: message,
        page_context: pageContext,
        book_title: BOOK_META.title,
        book_authors: BOOK_META.authors,
        book_description: BOOK_META.description,
        book_tags: BOOK_META.tags,
      }),
    }).then(function (resp) {
      if (!resp.ok) {
        return resp.text().then(function (t) {
          throw new Error("HTTP " + resp.status + ": " + t);
        });
      }
      var reader = resp.body.getReader();
      var decoder = new TextDecoder();
      var buffer = "";

      function pump() {
        reader.read().then(function (result) {
          if (result.done) { finishMessage(); return; }
          buffer += decoder.decode(result.value, { stream: true });
          var lines = buffer.split("\n");
          buffer = lines.pop(); // keep partial line
          for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (line.indexOf("data:") !== 0) continue;
            var payload = line.slice(5).trim();
            if (payload === "[DONE]") { finishMessage(); return; }
            try {
              var obj = JSON.parse(payload);
              if (obj.delta) {
                fullText += obj.delta;
                $msg.html(renderMarkdown(fullText));
                scrollMessages();
              }
              if (obj.error) {
                fullText += "\n[Error: " + obj.error + "]";
                $msg.html(renderMarkdown(fullText));
              }
            } catch (e) { /* ignore parse errors on partial chunks */ }
          }
          pump();
        }).catch(function (err) {
          finishMessage("Error: " + err.message);
        });
      }
      pump();
    }).catch(function (err) {
      finishMessage("Error: " + err.message);
    });

    function finishMessage(errMsg) {
      if (errMsg && !fullText) {
        $msg.html('<span class="ai-chat-typing">' + errMsg + '</span>');
      } else if (!fullText) {
        $msg.html('<span class="ai-chat-typing">(no response)</span>');
      }
      sending = false;
      $("#ai-chat-send").prop("disabled", false);
    }
  }

  $(init);
})(jQuery);
```

- [ ] **Step 4: Create the chat panel template**

`cps/templates/ai_chat_panel.html`:
```html
{# AI Companion chat panel — included by reader templates (read.html, readpdf.html, readtxt.html).
   Adds a floating button (bottom-right) that opens a right-side chat drawer.
   Depends on jQuery (already loaded by all reader templates). #}
<link rel="stylesheet" href="{{ url_for('static', filename='css/ai_chat.css') }}">
<div id="ai-companion-root">
  <button id="ai-companion-fab" title="{{_('AI Companion')}}">AI</button>
  <div id="ai-companion-drawer">
    <header>
      <h3>{{_('AI Reading Companion')}}</h3>
      <button id="ai-companion-close">&times;</button>
    </header>
    <div id="ai-chat-messages"></div>
    <div id="ai-chat-input-area">
      <textarea id="ai-chat-input" placeholder="{{_('Ask about the current page...')}}"></textarea>
      <button id="ai-chat-send">{{_('Send')}}</button>
    </div>
  </div>
</div>
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
<script>
  // Pass book metadata to JS so it can be included in chat requests
  window.AICompanionBookMeta = {
    title: "{{ title|e }}",
    authors: [],
    description: "",
    tags: []
  };
</script>
<script src="{{ url_for('static', filename='js/ai_page_extract.js') }}"></script>
<script src="{{ url_for('static', filename='js/ai_chat.js') }}"></script>
```

- [ ] **Step 5: Commit**

```bash
git add cps/static/css/ai_chat.css cps/static/js/ai_page_extract.js cps/static/js/ai_chat.js cps/templates/ai_chat_panel.html
git commit -m "feat(ai): add chat panel frontend (CSS, JS, page extraction, template)"
```

---

## Task 9: Inject the chat panel into reader templates

**Files:**
- Modify: `cps/templates/read.html` (1 line)
- Modify: `cps/templates/readpdf.html` (1 line)
- Modify: `cps/templates/readtxt.html` (1 line)

- [ ] **Step 1: Add the include to read.html**

In `/workspace/cps/templates/read.html`, add this line immediately before the closing `</body>` tag (line 494):

```html
    {% include 'ai_chat_panel.html' %}
```

The closing `</body>` is on line 494. The include should go right before it (after the last `<script>` tag for epub.js).

- [ ] **Step 2: Add the include to readpdf.html**

In `/workspace/cps/templates/readpdf.html`, add the same line immediately before `</body>`. Read the file first to find the exact closing `</body>` location.

- [ ] **Step 3: Add the include to readtxt.html**

In `/workspace/cps/templates/readtxt.html`, add the same line immediately before `</body>` (line 33).

```html
    {% include 'ai_chat_panel.html' %}
```

- [ ] **Step 4: Manual verification — open an epub book reader and confirm the AI button appears**

Run the dev server, log in, open any epub book, and verify the "AI" floating button appears in the bottom-right corner. Click it to confirm the drawer opens. (The chat won't work until the AI provider is configured in /ai/admin, but the UI should render.)

- [ ] **Step 5: Commit**

```bash
git add cps/templates/read.html cps/templates/readpdf.html cps/templates/readtxt.html
git commit -m "feat(ai): inject AI companion panel into epub/pdf/txt reader templates"
```

---

## Task 10: Authentik OAuth provider

**Files:**
- Create: `cps/ai/authentik.py`
- Modify: `cps/main.py` (the `register_authentik` call was already added in Task 7)
- Test: `tests/test_authentik.py`

- [ ] **Step 1: Write the failing test**

`tests/test_authentik.py`:
```python
"""Tests for the Authentik OAuth integration."""
from unittest.mock import patch, MagicMock


class TestAuthentik:
    def test_register_authentik_no_config(self, app):
        """register_authentik should be a no-op when authentik is not configured."""
        from cps.ai.authentik import register_authentik
        # Should not raise even if no authentik provider row exists
        register_authentik(app)
        # The /login/authentik route may or may not be registered depending on config

    def test_register_authentik_with_config(self, app):
        """When authentik config is present, the blueprint should register."""
        from cps.ub import session
        from cps.ai.models import AiProvider
        import json
        # Add an authentik provider row
        prov = AiProvider()
        prov.provider_name = "authentik"
        prov.display_name = "Authentik"
        prov.api_base = "https://auth.example.com/application/o/calibre-web/"
        prov.api_key_encrypted = ""  # client_id stored separately for now
        prov.models_json = "[]"
        prov.active = True
        session.add(prov)
        session.commit()

        from cps.ai.authentik import register_authentik
        register_authentik(app)

        # The login route should now exist
        rules = [r.rule for r in app.url_map.iter_rules()]
        assert any("/login/authentik" in r for r in rules)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_authentik.py -v`
Expected: FAIL with `ImportError: cannot import name 'register_authentik'`

- [ ] **Step 3: Create cps/ai/authentik.py**

`cps/ai/authentik.py`:
```python
"""Authentik OAuth2 login provider for calibre-web.

Uses flask-dance's generic OAuth2ConsumerBlueprint (flask-dance is already an
optional dependency) to support Authentik as an OAuth2/OIDC provider. Authentik
follows standard OAuth2 endpoints:
  authorize:  /application/o/authorize/
  token:      /application/o/token/
  userinfo:   /application/o/userinfo/

The blueprint is registered only if an `authentik` AiProvider row exists and is
active. Tokens are stored in the existing `ub.OAuth` table (same as github/google)
so the existing `bind_oauth_or_register()` flow handles user linking.

Config is stored in the AiProvider table:
  api_base        -> Authentik application base URL (e.g. https://auth.example.com/application/o/calibre-web/)
  api_key_encrypted -> client_id (encrypted) — reuses the same field
  models_json     -> JSON with {"client_secret_encrypted": "..."} (storing the secret)
                     (This is a slight abuse of the models_json field to avoid adding
                      a new column, keeping the schema stable.)

This module is intentionally self-contained: it does NOT modify cps/oauth_bb.py.
"""
import json
import logging

from flask import redirect, url_for, flash, session
from flask_babel import gettext as _
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.oauth2 import OAuth2ConsumerBlueprint
from oauthlib.oauth2 import TokenExpiredError, InvalidGrantError

from cps import app, ub, logger
from cps.cw_login import login_user, current_user
from cps.usermanagement import user_login_required
from sqlalchemy.orm.exc import NoResultFound

from .models import AiProvider
from .crypto import decrypt_value, encrypt_value

log = logger.create()

_AUTHENTIK_BLUEPRINT = None


def _get_authentik_config():
    """Return (client_id, client_secret, base_url) or None if not configured."""
    try:
        prov = ub.session.query(AiProvider).filter_by(provider_name="authentik", active=True).first()
        if prov is None or not prov.api_base:
            return None
        # Get encryption key
        from cps import config_sql
        import os
        settings_path = os.path.dirname(ub.app_DB_path)
        key, _ = config_sql.get_encryption_key(settings_path)

        client_id = decrypt_value(prov.api_key_encrypted, key)
        client_secret = ""
        try:
            extra = json.loads(prov.models_json or "{}")
            client_secret = decrypt_value(extra.get("client_secret_encrypted", ""), key)
        except (json.JSONDecodeError, TypeError):
            pass
        return client_id, client_secret, prov.api_base
    except Exception as e:
        log.warning("authentik config read failed: %s", e)
        return None


def register_authentik(flask_app):
    """Register the Authentik OAuth2 blueprint if configured.

    Called from cps/main.py. Safe to call when authentik is not configured —
    it will be a no-op.
    """
    global _AUTHENTIK_BLUEPRINT
    config = _get_authentik_config()
    if config is None:
        log.info("Authentik OAuth not configured, skipping blueprint registration")
        return

    client_id, client_secret, base_url = config
    base_url = base_url.rstrip("/")

    blueprint = OAuth2ConsumerBlueprint(
        "authentik",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        base_url=base_url + "/",
        authorization_url=base_url + "/authorize/",
        token_url=base_url + "/token/",
        scope=["openid", "email", "profile"],
        redirect_to="authentik.login_authentik",
    )

    # Use the same OAuthBackend as github/google for token storage
    try:
        from cps.oauth import OAuthBackend
        # Find or create an OAuthProvider row for authentik
        oauth_prov = ub.session.query(ub.OAuthProvider).filter_by(provider_name="authentik").first()
        if oauth_prov is None:
            oauth_prov = ub.OAuthProvider()
            oauth_prov.provider_name = "authentik"
            oauth_prov.active = True
            ub.session.add(oauth_prov)
            ub.session.commit()
        blueprint.backend = OAuthBackend(ub.OAuth, ub.session, str(oauth_prov.id),
                                         user=current_user, user_required=True)
    except Exception as e:
        log.warning("authentik backend setup failed: %s", e)

    flask_app.register_blueprint(blueprint, url_prefix="/login")
    _AUTHENTIK_BLUEPRINT = blueprint

    @oauth_authorized.connect_via(blueprint)
    def authentik_logged_in(bp, token):
        if not token:
            flash(_("Failed to log in with Authentik."), category="error")
            return False
        resp = bp.session.get("/userinfo")
        if not resp.ok:
            flash(_("Failed to fetch user info from Authentik."), category="error")
            return False
        info = resp.json()
        authentik_user_id = str(info.get("sub") or info.get("id") or "")
        if not authentik_user_id:
            flash(_("Authentik did not return a user id."), category="error")
            return False

        # Reuse calibre-web's existing bind-or-register logic
        from cps.oauth_bb import oauth_update_token, bind_oauth_or_register, oauth_check
        # Register the provider in oauth_check if not present
        if str(oauth_prov.id) not in oauth_check:
            oauth_check[str(oauth_prov.id)] = "authentik"

        oauth_update_token(str(oauth_prov.id), token, authentik_user_id)
        return bind_oauth_or_register(str(oauth_prov.id), authentik_user_id,
                                      "authentik.login_authentik", "Authentik")

    # Add the login route handler on this module
    import sys
    mod = sys.modules[__name__]

    @mod.route("/link/authentik", endpoint="login_authentik")
    @user_login_required
    def login_authentik():
        if not blueprint.session.authorized:
            return redirect(url_for("authentik.login"))
        try:
            resp = blueprint.session.get("/userinfo")
            if resp.ok:
                info = resp.json()
                authentik_user_id = str(info.get("sub") or info.get("id") or "")
                from cps.oauth_bb import bind_oauth_or_register
                oauth_prov = ub.session.query(ub.OAuthProvider).filter_by(provider_name="authentik").first()
                return bind_oauth_or_register(str(oauth_prov.id), authentik_user_id,
                                              "authentik.login", "Authentik")
            flash(_("Authentik OAuth error, please retry later."), category="error")
        except (InvalidGrantError, TokenExpiredError) as e:
            flash(_("Authentik OAuth error: {}").format(e), category="error")
        return redirect(url_for("web.login"))

    log.info("Authentik OAuth blueprint registered")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_authentik.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add cps/ai/authentik.py tests/test_authentik.py
git commit -m "feat(ai): add Authentik OAuth2 login provider via flask-dance"
```

---

## Task 11: Add AI Settings link to admin navigation

**Files:**
- Modify: `cps/templates/layout.html` (1 line, conditional)

- [ ] **Step 1: Add the AI Settings link in the admin nav**

Read `/workspace/cps/templates/layout.html` around line 92-94 (where the admin link is). After the existing admin link block:

```html
{% if current_user.role_admin() %}
  <li><a id="top_admin" data-text="{{_('Settings')}}" href="{{url_for('admin.admin')}}"><span class="glyphicon glyphicon-dashboard"></span> <span class="hidden-sm">{{_('Admin')}}</span></a></li>
{% endif %}
```

Add immediately after it:

```html
{% if current_user.role_admin() %}
  <li><a id="top_ai_admin" href="{{url_for('aichat.admin')}}" title="{{_('AI Companion Settings')}}"><span class="glyphicon glyphicon-comment"></span> <span class="hidden-sm">{{_('AI')}}</span></a></li>
{% endif %}
```

- [ ] **Step 2: Verify the link appears for admin users**

Run the dev server, log in as admin, and confirm the "AI" link appears in the top nav bar next to "Admin". Click it to confirm it reaches `/ai/admin`.

- [ ] **Step 3: Commit**

```bash
git add cps/templates/layout.html
git commit -m "feat(ai): add AI Settings link to admin navigation"
```

---

## Task 12: Add authentik provider config to the AI admin page

**Files:**
- Modify: `cps/ai/routes.py` (extend the admin POST handler to seed authentik provider row)
- Modify: `cps/templates/ai_admin.html` (add authentik-specific fields)

- [ ] **Step 1: Extend the admin route to handle authentik client_secret**

In `/workspace/cps/ai/routes.py`, inside the `admin()` POST handler, after the provider loop, add handling for the authentik client_secret. The authentik provider uses `models_json` to store `{"client_secret_encrypted": "..."}`.

Add this block inside the POST handler's provider loop (where `prov.models_json` is set):

```python
            # For authentik, also store the client_secret in models_json
            if prov.provider_name == "authentik":
                new_secret = request.form.get(field_prefix + "client_secret", "")
                extra = {}
                try:
                    extra = json.loads(prov.models_json or "{}")
                except (json.JSONDecodeError, TypeError):
                    extra = {}
                if new_secret:
                    extra["client_secret_encrypted"] = encrypt_value(new_secret, key)
                # Preserve models_json as the extra dict (authentik has no model list)
                prov.models_json = json.dumps(extra)
```

- [ ] **Step 2: Update the admin template to show authentik client_secret field**

In `/workspace/cps/templates/ai_admin.html`, inside the provider loop panel, add a conditional field for authentik:

After the API Key field block, add:

```html
            {% if prov.provider_name == "authentik" %}
            <div class="form-group">
              <label>{{_('Client Secret')}}</label>
              <input type="password" name="provider_{{ prov.id }}_client_secret" class="form-control" placeholder="{{_('Leave blank to keep current')}}">
            </div>
            {% else %}
            <div class="form-group">
              <label>{{_('Models (one per line, format: id|label)')}}</label>
              <textarea name="provider_{{ prov.id }}_models" class="form-control" rows="3">{% set models = prov.models_json | from_json %}{% for m in models %}{{ m.id }}|{{ m.label }}
{% endfor %}</textarea>
            </div>
            {% endif %}
```

- [ ] **Step 3: Verify the admin page shows authentik fields when an authentik provider row exists**

Run the dev server, go to `/ai/admin`. The deepseek provider should show the Models textarea; if you manually add an "authentik" row to the AiProvider table (or it gets created when register_authentik runs), the authentik provider should show the Client Secret field instead.

- [ ] **Step 4: Commit**

```bash
git add cps/ai/routes.py cps/templates/ai_admin.html
git commit -m "feat(ai): add authentik client_secret config to admin page"
```

---

## Task 13: End-to-end integration test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write an integration test that exercises the full chat flow**

`tests/test_integration.py`:
```python
"""End-to-end integration test: configure provider, send a chat message, verify
history is persisted and memory is extracted."""
from unittest.mock import patch, MagicMock
import json


class TestIntegration:
    def test_full_chat_flow(self, admin_client, app):
        from cps.ai.models import AiConfig, AiProvider, AiMessage, AiUserMemory
        from cps.ub import session
        from cps.ai.crypto import encrypt_value

        # 1. Enable AI and set a fake deepseek key
        cfg = session.query(AiConfig).first()
        cfg.enabled = True
        cfg.memory_enabled = True
        cfg.memory_extract_interval = 2  # extract after every 2 messages
        session.commit()

        # 2. Mock the provider to return a canned response
        fake_provider = MagicMock()
        # chat() is called once for the actual reply (streaming), once for memory extraction (non-stream)
        fake_provider.chat.side_effect = [
            iter(["Reply "]),       # streaming reply to message 1
            "User likes sci-fi",     # memory extraction after message 2 (user + assistant = 2 msgs)
            iter(["Reply 2"]),       # streaming reply to message 2
        ]

        with patch("cps.ai.routes.get_active_provider", return_value=(fake_provider, "deepseek-chat")):
            # First message
            rv = admin_client.post("/ai/chat", json={
                "book_id": 1, "book_format": "EPUB",
                "message": "What is this book about?",
                "page_context": "Chapter 1 text",
            })
            assert rv.status_code == 200
            assert b"Reply " in rv.data

            # Second message (triggers memory extraction since interval=2)
            rv = admin_client.post("/ai/chat", json={
                "book_id": 1, "book_format": "EPUB",
                "message": "Tell me more",
                "page_context": "Chapter 2 text",
            })
            assert rv.status_code == 200

        # 3. Verify history was persisted
        rv = admin_client.get("/ai/history/1")
        data = rv.get_json()
        assert len(data["messages"]) == 4  # 2 user + 2 assistant

        # 4. Verify memory was extracted (at least one AiUserMemory row)
        # Note: memory extraction happens after the 2nd message pair (4 messages total)
        mems = session.query(AiUserMemory).filter_by(user_id=1).all()
        # The exact timing depends on should_extract_memory(4, 2) — should be True
        assert len(mems) >= 1
        assert mems[0].content == "User likes sci-fi"

    def test_clear_history_removes_messages(self, admin_client, app):
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
        rv = admin_client.get("/ai/history/99")
        data = rv.get_json()
        assert data["messages"] == []
```

- [ ] **Step 2: Run the integration test**

Run: `pytest tests/test_integration.py -v`
Expected: 2 passed

- [ ] **Step 3: Run the full test suite**

Run: `pytest tests/ -v`
Expected: all tests pass

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test(ai): add end-to-end integration test for chat flow with memory"
```

---

## Self-Review

### 1. Spec coverage

- ✅ **AI companion page on the reader** — Task 8 (frontend) + Task 9 (inject into read.html/readpdf.html/readtxt.html). Floating sidebar, sends book metadata + current page + question to AI.
- ✅ **AI memory system** — Task 5 (memory.py: build_system_prompt + extract_user_memory) + AiUserMemory table (Task 2). Cross-book memory (per-user, not per-book) injected into system prompt.
- ✅ **Authentik login** — Task 10 (authentik.py with flask-dance OAuth2ConsumerBlueprint) + Task 12 (admin config). Reuses existing ub.OAuth table and bind_oauth_or_register flow.
- ✅ **Multi-provider multi-model** — Task 3 (BaseProvider ABC) + Task 4 (registry) + AiProvider table (Task 2). Default: deepseek-chat. Admin can add providers/models. Adding a new provider = register_provider_class() + a new subclass.
- ✅ **DeepSeek support** — Task 3 (DeepSeekProvider with OpenAI-compatible API + SSE streaming).
- ✅ **Minimal intrusion** — Only 6 upstream files modified: main.py (3 lines), read.html (1 line), readpdf.html (1 line), readtxt.html (1 line), layout.html (1 line), pyproject.toml (pytest config). All AI code is in cps/ai/ subpackage.

### 2. Placeholder scan

- No "TBD", "TODO", "implement later" found.
- Every code step has actual code.
- Test code is complete, not stubbed.

### 3. Type consistency

- `get_active_provider()` returns `(provider, model)` tuple — used consistently in routes.py and tests.
- `build_system_prompt()` signature matches in memory.py (definition) and routes.py (call).
- `extract_user_memory()` signature: `(provider, model, recent_messages, user_id, book_id)` — consistent in memory.py and routes.py.
- `AiProvider` fields: `provider_name`, `api_base`, `api_key_encrypted`, `models_json`, `active`, `display_name` — used consistently in routes.py, authentik.py, and __init__.py seeding.
- `register_authentik(app)` — called in main.py (Task 7) and defined in authentik.py (Task 10).

### Gaps found and addressed during review

- The admin template in Task 6 uses a `from_json` Jinja filter that doesn't exist in calibre-web by default. Added Step 5 in Task 6 to register it in cps/jinjia.py.
- The authentik blueprint needs an OAuthProvider row for the OAuthBackend provider_id. Step 3 in Task 10 creates it if missing.
- The `register_authentik` import in main.py (Task 7) runs before any authentik config exists — wrapped in try/except ImportError and the function itself is a no-op when unconfigured.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-27-ai-reading-companion.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
