"""OpenAI-compatible text-to-speech synthesis for the reader.

Why a standalone module instead of a BaseProvider subclass:
- TTS speaks a different wire protocol (``/audio/speech`` returning binary
  audio) than chat providers (``/chat/completions`` returning JSON/SSE), and
  the admin UI stores it as a dedicated ``AiProvider`` row (provider_name
  ``tts``) whose ``models_json`` holds ``{"model", "voice"}`` instead of a
  model list — so it never goes through the chat provider registry.
- Gateways that speak the OpenAI TTS protocol (OpenAI tts-1, SiliconFlow
  CosyVoice, new-api, etc.) are all covered by one configurable ``api_base``.
"""
import hashlib
from collections import OrderedDict
from threading import Lock

import requests

DEFAULT_TIMEOUT = 120


def synthesize_speech(api_base, api_key, model, voice, text,
                      timeout=DEFAULT_TIMEOUT):
    """Synthesize ``text`` to mp3 bytes via ``{api_base}/audio/speech``.

    Raises ``RuntimeError`` with a truncated message on HTTP errors, JSON
    error bodies (some gateways answer 200 with an error object), or empty
    audio so callers can surface a readable message.
    """
    url = (api_base or "").rstrip("/") + "/audio/speech"
    payload = {"model": model, "input": text, "voice": voice,
               "response_format": "mp3"}
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(
            f"TTS API error {resp.status_code}: {resp.text[:300]}")
    content_type = resp.headers.get("Content-Type", "")
    # A JSON body on 200 means the gateway returned an error object instead
    # of audio; anything else (audio/*, octet-stream, empty) is accepted.
    if "json" in content_type.lower():
        raise RuntimeError(
            f"TTS API returned an error response: {resp.text[:300]}")
    if not resp.content:
        raise RuntimeError("TTS API returned empty audio")
    return resp.content


def tts_cache_key(model, voice, text):
    """Cache key covering everything that changes the synthesized audio."""
    return hashlib.sha256(f"{model}|{voice}|{text}".encode("utf-8")).hexdigest()


class LruCache:
    """Thread-safe LRU cache (OrderedDict based)."""

    def __init__(self, capacity):
        self._capacity = capacity
        self._data = OrderedDict()
        self._lock = Lock()

    def get(self, key):
        with self._lock:
            if key not in self._data:
                return None
            self._data.move_to_end(key)
            return self._data[key]

    def put(self, key, value):
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            while len(self._data) > self._capacity:
                self._data.popitem(last=False)

    def clear(self):
        with self._lock:
            self._data.clear()


#: Module-level audio cache: re-reading the same paragraph (page turn back,
#: replay) must not re-synthesize. 128 mp3 paragraphs ≈ tens of MB at most.
TTS_CACHE = LruCache(128)
