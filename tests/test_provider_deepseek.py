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
        # Every ModelInfo should have an id and label
        for m in models:
            assert isinstance(m, ModelInfo)
            assert m.id
            assert m.label

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
        # Verify the API was called with the OpenAI-compatible endpoint.
        # requests.post(url, headers=..., json=..., stream=True, timeout=...)
        # — url is the first positional arg, headers/json/stream/timeout are kwargs.
        call_args = mock_post.call_args
        url = call_args[0][0] if call_args.args else call_args[1].get("url")
        assert "/chat/completions" in url
        headers = call_args.kwargs.get("headers") or call_args[1].get("headers")
        assert headers["Authorization"] == "Bearer sk-test"
        body = call_args.kwargs.get("json") or call_args[1].get("json")
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
        fake_response.__enter__ = MagicMock(return_value=fake_response)
        fake_response.__exit__ = MagicMock(return_value=False)
        with patch("cps.ai.deepseek.requests.post", return_value=fake_response):
            with pytest.raises(RuntimeError, match="DeepSeek API error 401"):
                list(p.chat([{"role": "user", "content": "hi"}], model="deepseek-chat"))

    def test_chat_passes_through_extra_kwargs(self):
        """Extra kwargs like temperature should be passed in the request body."""
        p = DeepSeekProvider(api_base="https://api.deepseek.com", api_key="sk-test")
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json = MagicMock(return_value={
            "choices": [{"message": {"content": "ok"}}]
        })
        with patch("cps.ai.deepseek.requests.post", return_value=fake_response) as mock_post:
            p.chat([{"role": "user", "content": "hi"}],
                   model="deepseek-chat", stream=False, temperature=0.7)
        body = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert body["temperature"] == 0.7
