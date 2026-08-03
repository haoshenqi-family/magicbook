"""Tests for the AI memory system."""
from unittest.mock import patch, MagicMock

import pytest

from cps.ai.memory import (
    build_system_prompt, extract_user_memory, get_user_memory_strings,
    should_extract_memory,
)


class TestBuildSystemPrompt:
    def test_includes_book_metadata(self):
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

    def test_includes_extra_prompt(self):
        prompt = build_system_prompt(
            book_title="T", book_authors=[], book_description="",
            book_tags=[], page_context="", user_memory=[],
            extra_prompt="Always answer in haiku form.",
        )
        assert "haiku" in prompt

    def test_strips_html_from_description(self):
        prompt = build_system_prompt(
            book_title="T", book_authors=[], book_description="<p>An <b>epic</b> tale.</p>",
            book_tags=[], page_context="", user_memory=[], extra_prompt="",
        )
        assert "<p>" not in prompt
        assert "<b>" not in prompt
        assert "epic" in prompt

    def test_truncates_long_page_context(self):
        long_text = "x" * 20000
        prompt = build_system_prompt(
            book_title="T", book_authors=[], book_description="",
            book_tags=[], page_context=long_text, user_memory=[], extra_prompt="",
        )
        assert "truncated" in prompt
        # Should be much shorter than the original 20k chars
        assert len(prompt) < 12000

    def test_handles_empty_inputs(self):
        prompt = build_system_prompt(
            book_title="", book_authors=[], book_description="",
            book_tags=[], page_context="", user_memory=[], extra_prompt="",
        )
        # Should still produce a valid prompt
        assert "reading companion" in prompt.lower()


class TestShouldExtractMemory:
    def test_extracts_at_interval(self):
        assert should_extract_memory(message_count=10) is True
        assert should_extract_memory(message_count=20, interval=10) is True

    def test_does_not_extract_between_intervals(self):
        assert should_extract_memory(message_count=9, interval=10) is False
        assert should_extract_memory(message_count=15, interval=10) is False

    def test_zero_interval_disables_extraction(self):
        assert should_extract_memory(message_count=10, interval=0) is False

    def test_zero_messages_does_not_extract(self):
        assert should_extract_memory(message_count=0, interval=10) is False


class TestExtractUserMemory:
    def test_calls_provider_and_returns_string(self):
        """extract_user_memory should call the provider and return a memory string."""
        fake_provider = MagicMock()
        # Non-streaming call returns a string
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
        first_msg_content = call_messages[0]["content"].lower()
        assert "extract" in first_msg_content or "insight" in first_msg_content

    def test_returns_none_when_provider_says_none(self):
        fake_provider = MagicMock()
        fake_provider.chat.return_value = "NONE"
        result = extract_user_memory(
            provider=fake_provider, model="deepseek-chat",
            recent_messages=[{"role": "user", "content": "hi"}],
            user_id=1, book_id=1,
        )
        assert result is None

    def test_returns_none_on_provider_exception(self):
        fake_provider = MagicMock()
        fake_provider.chat.side_effect = RuntimeError("API down")
        result = extract_user_memory(
            provider=fake_provider, model="deepseek-chat",
            recent_messages=[{"role": "user", "content": "hi"}],
            user_id=1, book_id=1,
        )
        assert result is None


class TestGetUserMemoryStrings:
    def test_returns_user_memories(self, app, ai_session):
        from cps.ai.models import AiUserMemory
        m1 = AiUserMemory(user_id=1, content="Likes sci-fi", source_book_id=1)
        m2 = AiUserMemory(user_id=1, content="Prefers concise answers", source_book_id=2)
        m3 = AiUserMemory(user_id=2, content="Other user's memory", source_book_id=1)
        ai_session.add_all([m1, m2, m3])
        ai_session.commit()

        mems = get_user_memory_strings(user_id=1, limit=10)
        assert "Likes sci-fi" in mems
        assert "Prefers concise answers" in mems
        assert "Other user's memory" not in mems
        assert len(mems) == 2

    def test_returns_empty_for_unknown_user(self, app):
        mems = get_user_memory_strings(user_id=99999, limit=10)
        assert mems == []

    def test_stores_extracted_memory_in_db(self, app, ai_session):
        """extract_user_memory should persist the extracted memory in AiUserMemory."""
        from cps.ai.models import AiUserMemory

        fake_provider = MagicMock()
        fake_provider.chat.return_value = "User likes deep dives"

        extract_user_memory(
            provider=fake_provider, model="deepseek-chat",
            recent_messages=[{"role": "user", "content": "explain in detail"}],
            user_id=7, book_id=99,
        )

        stored = ai_session.query(AiUserMemory).filter_by(user_id=7).all()
        assert len(stored) == 1
        assert stored[0].content == "User likes deep dives"
        assert stored[0].source_book_id == 99
