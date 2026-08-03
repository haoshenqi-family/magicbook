"""AI memory system: system-prompt construction + cross-book memory extraction.

Two responsibilities:
1. ``build_system_prompt()`` — assembles the system prompt sent to the LLM
   from book metadata, current page text, and the user's long-term memories.
2. ``extract_user_memory()`` — calls the LLM with recent conversation messages
   and asks it to produce a concise insight about the user; the result is
   stored in ``AiUserMemory`` for injection into future conversations.
"""
import re
from typing import List, Optional

from cps import logger

from .models import AiUserMemory

log = logger.create()


def _session():
    """Lazy access to the AI data session — read at call time, not import time,
    so this module can be imported before create_app() initializes the data layer."""
    from .database import get_session
    return get_session()

_MAX_PAGE_CHARS = 8000
_MAX_DESC_CHARS = 1000
_MAX_RECENT_MESSAGES = 12


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
    if len(page_context) > _MAX_PAGE_CHARS:
        page_context = page_context[:_MAX_PAGE_CHARS] + "\n...[truncated]"

    parts = [
        "You are an AI reading companion helping the user understand a book they are currently reading.",
        "Answer questions, explain passages, and discuss themes based on the book's metadata and the current page text provided below.",
        "Be concise and helpful. If the user's question is unrelated to the book, gently redirect.",
        "",
        "## Book Metadata",
        f"Title: {book_title}",
        f"Author(s): {authors_str}",
    ]
    if tags_str:
        parts.append(f"Tags: {tags_str}")
    if book_description:
        # Strip HTML from description (calibre stores it as HTML)
        desc = re.sub(r"<[^>]+>", "", book_description).strip()
        if len(desc) > _MAX_DESC_CHARS:
            desc = desc[:_MAX_DESC_CHARS] + "..."
        parts.append(f"Description: {desc}")
    parts.extend([
        "",
        "## Current Page Text",
        page_context if page_context else "(no page context provided)",
        "",
        "## What you remember about this user (long-term memory)",
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

    Stores the result in ``AiUserMemory`` and returns the extracted string
    (or None if nothing worth remembering was found).
    """
    extraction_prompt = (
        "You are a memory assistant. Read the following conversation between a user and an AI reading companion. "
        "Extract ONE concise sentence capturing a durable insight about this user — their reading preferences, "
        "interests, knowledge level, or what they care about. "
        "Output only the sentence, no preamble. If there is nothing worth remembering, output exactly: NONE"
    )
    messages = [{"role": "system", "content": extraction_prompt}]
    # Include up to the last N messages of context
    for m in recent_messages[-_MAX_RECENT_MESSAGES:]:
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
        ub_session = _session()
        mem = AiUserMemory()
        mem.user_id = user_id
        mem.content = result
        mem.source_book_id = book_id
        ub_session.add(mem)
        ub_session.commit()
    except Exception as e:
        log.warning("failed to store user memory: %s", e)
        try:
            ub_session.rollback()
        except Exception:
            pass

    return result


def get_user_memory_strings(user_id: int, limit: int = 20) -> List[str]:
    """Return the user's long-term memory entries as a list of strings (newest first)."""
    try:
        ub_session = _session()
        mems = ub_session.query(AiUserMemory).filter_by(user_id=user_id)\
            .order_by(AiUserMemory.created_at.desc()).limit(limit).all()
        return [m.content for m in mems]
    except Exception as e:
        log.warning("failed to load user memory: %s", e)
        return []
