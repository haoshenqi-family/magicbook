"""DeepSeek provider — calls the OpenAI-compatible /chat/completions endpoint.

DeepSeek's API (https://api.deepseek.com) is OpenAI-compatible, so we use the
standard ``/chat/completions`` path with ``stream: true`` for SSE streaming.

The provider is configured at runtime from an ``AiProvider`` DB row
(api_base + decrypted api_key). It supports both streaming (generator) and
non-streaming (full string) modes.
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
