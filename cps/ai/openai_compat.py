"""Generic OpenAI-compatible provider.

Why a generic provider instead of a per-vendor one:
- Many LLM gateways (OpenAI, Azure OpenAI via compatible endpoints, local
  Ollama/vLLM, OneAPI, new-api, etc.) speak the same ``/chat/completions``
  protocol. One provider class + a configurable ``api_base`` covers them all,
  so users don't need a new Python module per vendor.
- Model list is configured in the admin UI (``AiProvider.models_json``) because
  a compatible endpoint may not expose ``/models`` (or may require extra auth).
  We still make a best-effort attempt to list models from ``/models`` when an
  api_key is present.

The class mirrors DeepSeek's OpenAI-compatible implementation but with a
vendor-agnostic name and error messages.
"""
import json
from typing import Dict, Generator, List, Union

import requests

from .base import BaseProvider, ModelInfo


class OpenAICompatProvider(BaseProvider):
    """Chat provider for any OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(self, api_base: str, api_key: str, timeout: int = 120):
        self._api_base = (api_base or "").rstrip("/")
        self._api_key = api_key or ""
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "openai"

    #: OpenAI-compatible gateways may be keyless (local Ollama/vLLM, etc.).
    requires_key = False

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def available_models(self) -> List[ModelInfo]:
        """Best-effort fetch of model ids from ``/models``.

        Returns an empty list when the endpoint is unreachable, requires auth we
        don't have, or doesn't implement ``/models`` — the admin UI is the
        source of truth for the model list in those cases.
        """
        if not self._api_base or not self._api_key:
            return []
        try:
            resp = requests.get(f"{self._api_base}/models",
                                headers=self._headers(), timeout=self._timeout)
            if resp.status_code != 200:
                return []
            data = resp.json()
            models = data.get("data", []) if isinstance(data, dict) else []
            out = []
            for m in models:
                # Defensive: tolerate endpoints that return a flat list of
                # model id strings instead of the standard {"id": ...} objects.
                if isinstance(m, dict) and m.get("id"):
                    out.append(ModelInfo(id=m["id"]))
                elif isinstance(m, str) and m.strip():
                    out.append(ModelInfo(id=m.strip()))
            return out
        except (requests.RequestException, ValueError, AttributeError, TypeError):
            return []

    def chat(self, messages: List[Dict[str, str]], model: str,
             stream: bool = True, **kwargs) -> Union[Generator[str, None, None], str]:
        url = f"{self._api_base}/chat/completions"
        # Apply extra kwargs first, then force the reserved fields so callers
        # can never accidentally override model/messages/stream.
        payload = {"model": model, "messages": messages, "stream": stream}
        payload.update(kwargs)
        payload["model"] = model
        payload["messages"] = messages
        payload["stream"] = stream

        if stream:
            return self._stream_chat(url, payload)
        return self._blocking_chat(url, payload)

    def _stream_chat(self, url, payload) -> Generator[str, None, None]:
        with requests.post(url, headers=self._headers(), json=payload,
                           stream=True, timeout=self._timeout) as resp:
            if resp.status_code != 200:
                raise RuntimeError(
                    f"OpenAI-compatible API error {resp.status_code}: {resp.text}"
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
                    # Some gateways return {"error": ...} with a 200 status;
                    # surface it instead of silently swallowing the stream.
                    if isinstance(chunk, dict) and chunk.get("error"):
                        raise RuntimeError(
                            f"OpenAI-compatible API error: {chunk['error']}")
                    delta = chunk["choices"][0].get("delta", {}).get("content", "")
                    if delta:
                        yield delta
                except json.JSONDecodeError:
                    continue
                except (KeyError, IndexError):
                    continue

    def _blocking_chat(self, url, payload) -> str:
        resp = requests.post(url, headers=self._headers(), json=payload,
                             timeout=self._timeout)
        if resp.status_code != 200:
            raise RuntimeError(
                f"OpenAI-compatible API error {resp.status_code}: {resp.text}"
            )
        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as e:
            raise RuntimeError(
                f"OpenAI-compatible API error: malformed response: {e}") from e
