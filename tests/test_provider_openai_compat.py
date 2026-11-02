"""Tests for the generic OpenAI-compatible provider (HTTP mocked)."""
import json
from unittest.mock import patch, MagicMock

import pytest

from cps.ai.base import ModelInfo
from cps.ai.openai_compat import OpenAICompatProvider


class TestOpenAICompatProvider:
    def test_provider_name(self):
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1",
                                 api_key="sk-test")
        assert p.name == "openai"

    def test_available_models_empty_without_key(self):
        """Without an api_key we must not try to list models."""
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1", api_key="")
        assert p.available_models() == []

    def test_available_models_fetches_from_models_endpoint(self):
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1",
                                 api_key="sk-test")
        fake = MagicMock()
        fake.status_code = 200
        fake.json = MagicMock(return_value={
            "data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}, {"object": "x"}]
        })
        with patch("cps.ai.openai_compat.requests.get", return_value=fake) as mock_get:
            models = p.available_models()
        assert [m.id for m in models] == ["gpt-4o", "gpt-4o-mini"]
        assert all(isinstance(m, ModelInfo) for m in models)
        mock_get.assert_called_once()
        assert "/models" in mock_get.call_args[0][0]

    def test_available_models_empty_on_error(self):
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1",
                                 api_key="sk-test")
        fake = MagicMock()
        fake.status_code = 404
        with patch("cps.ai.openai_compat.requests.get", return_value=fake):
            assert p.available_models() == []

    def test_chat_stream_yields_deltas(self):
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1",
                                 api_key="sk-test")
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

        with patch("cps.ai.openai_compat.requests.post", return_value=fake_response) as mock_post:
            chunks = list(p.chat([{"role": "user", "content": "hi"}],
                                 model="gpt-4o"))
        assert chunks == ["Hello", " world"]
        call_args = mock_post.call_args
        url = call_args[0][0] if call_args.args else call_args[1].get("url")
        assert url == "https://gateway.example.com/v1/chat/completions"
        headers = call_args.kwargs.get("headers") or call_args[1].get("headers")
        assert headers["Authorization"] == "Bearer sk-test"
        body = call_args.kwargs.get("json") or call_args[1].get("json")
        assert body["model"] == "gpt-4o"
        assert body["stream"] is True

    def test_chat_non_stream_returns_full(self):
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1/",
                                 api_key="sk-test")
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json = MagicMock(return_value={
            "choices": [{"message": {"content": "Full reply"}}]
        })
        with patch("cps.ai.openai_compat.requests.post", return_value=fake_response) as mock_post:
            result = p.chat([{"role": "user", "content": "hi"}],
                            model="gpt-4o", stream=False)
        assert result == "Full reply"
        # Trailing slash on api_base must not produce a double slash in the URL.
        url = mock_post.call_args[0][0]
        assert url == "https://gateway.example.com/v1/chat/completions"
        assert "//chat" not in url

    def test_chat_raises_on_http_error(self):
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1",
                                 api_key="sk-test")
        fake_response = MagicMock()
        fake_response.status_code = 401
        fake_response.text = "Unauthorized"
        fake_response.__enter__ = MagicMock(return_value=fake_response)
        fake_response.__exit__ = MagicMock(return_value=False)
        with patch("cps.ai.openai_compat.requests.post", return_value=fake_response):
            with pytest.raises(RuntimeError, match="OpenAI-compatible API error 401"):
                list(p.chat([{"role": "user", "content": "hi"}], model="gpt-4o"))

    def test_chat_without_key_omits_auth_header(self):
        """Compatible endpoints may need no auth (e.g. local Ollama)."""
        p = OpenAICompatProvider(api_base="http://localhost:11434/v1", api_key="")
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json = MagicMock(return_value={
            "choices": [{"message": {"content": "ok"}}]
        })
        with patch("cps.ai.openai_compat.requests.post", return_value=fake_response) as mock_post:
            p.chat([{"role": "user", "content": "hi"}], model="llama3", stream=False)
        headers = mock_post.call_args.kwargs.get("headers") or mock_post.call_args[1].get("headers")
        assert "Authorization" not in headers

    def test_requires_key_is_false(self):
        p = OpenAICompatProvider(api_base="http://localhost:11434/v1", api_key="")
        assert p.requires_key is False

    def test_chat_stream_surfaces_error_block(self):
        """A 200 SSE stream carrying an error block must raise, not go silent."""
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1",
                                 api_key="sk-test")
        sse_lines = [
            b'data: {"error":{"message":"rate limited","type":"rate_limit"}}\n\n',
        ]
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.iter_lines = MagicMock(return_value=iter(sse_lines))
        fake_response.__enter__ = MagicMock(return_value=fake_response)
        fake_response.__exit__ = MagicMock(return_value=False)
        with patch("cps.ai.openai_compat.requests.post", return_value=fake_response):
            with pytest.raises(RuntimeError, match="rate limited"):
                list(p.chat([{"role": "user", "content": "hi"}], model="gpt-4o"))

    def test_chat_non_stream_http_error(self):
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1",
                                 api_key="sk-test")
        fake_response = MagicMock()
        fake_response.status_code = 500
        fake_response.text = "boom"
        with patch("cps.ai.openai_compat.requests.post", return_value=fake_response):
            with pytest.raises(RuntimeError, match="OpenAI-compatible API error 500"):
                p.chat([{"role": "user", "content": "hi"}], model="gpt-4o", stream=False)

    def test_chat_non_stream_malformed_response(self):
        """Non-JSON / missing content should raise RuntimeError, not leak ValueError."""
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1",
                                 api_key="sk-test")
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json = MagicMock(side_effect=ValueError("no json"))
        with patch("cps.ai.openai_compat.requests.post", return_value=fake_response):
            with pytest.raises(RuntimeError, match="malformed response"):
                p.chat([{"role": "user", "content": "hi"}], model="gpt-4o", stream=False)

    def test_chat_non_stream_missing_choices(self):
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1",
                                 api_key="sk-test")
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json = MagicMock(return_value={"unexpected": True})
        with patch("cps.ai.openai_compat.requests.post", return_value=fake_response):
            with pytest.raises(RuntimeError, match="malformed response"):
                p.chat([{"role": "user", "content": "hi"}], model="gpt-4o", stream=False)

    def test_chat_merges_extra_kwargs_into_payload(self):
        """Extra kwargs (e.g. temperature) merge in; reserved fields stay intact.

        Python prevents a caller from passing model/messages/stream twice, so
        the meaningful assertion is that reserved fields are correct while
        extra kwargs appear in the request body.
        """
        p = OpenAICompatProvider(api_base="https://gateway.example.com/v1",
                                 api_key="sk-test")
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json = MagicMock(return_value={
            "choices": [{"message": {"content": "ok"}}]
        })
        with patch("cps.ai.openai_compat.requests.post", return_value=fake_response) as mock_post:
            p.chat([{"role": "user", "content": "hi"}], model="gpt-4o",
                   stream=False, temperature=0.7, top_p=0.9)
        body = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert body["model"] == "gpt-4o"
        assert body["stream"] is False
        assert body["messages"] == [{"role": "user", "content": "hi"}]
        assert body["temperature"] == 0.7
        assert body["top_p"] == 0.9
