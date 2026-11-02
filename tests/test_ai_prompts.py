"""Tests for the prompt template registry (cps/ai/prompts.py)."""
import pytest

from cps.ai.prompts import CHAT_SYSTEM, get_prompt, render_prompt


class TestGetPrompt:
    def test_returns_default_chat_system_template(self):
        template = get_prompt(CHAT_SYSTEM)
        assert "reading companion" in template
        assert "{{title}}" in template
        assert "{{chapter}}" in template
        assert "{{unfamiliar_words}}" in template

    def test_unknown_key_raises(self):
        with pytest.raises(KeyError):
            get_prompt("no-such-key")


class TestRenderPrompt:
    def test_replaces_provided_variables(self):
        rendered = render_prompt(CHAT_SYSTEM, title="Dune", chapter="Chapter 1")
        assert "Dune" in rendered
        assert "Chapter 1" in rendered
        assert "{{title}}" not in rendered
        assert "{{chapter}}" not in rendered

    def test_keeps_unprovided_placeholders(self):
        rendered = render_prompt(CHAT_SYSTEM)
        assert "{{title}}" in rendered

    def test_none_value_renders_empty(self):
        rendered = render_prompt(CHAT_SYSTEM, title=None)
        assert "{{title}}" not in rendered
