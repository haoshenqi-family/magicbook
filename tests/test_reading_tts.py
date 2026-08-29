"""Tests for reader paragraph TTS (/ai/tts, /ai/test_tts) and the batch
translation proxy (/ajax/reading-translate-batch).
"""
import json
from unittest.mock import patch, MagicMock

import pytest

from cps.ai.models import AiProvider


MP3 = b"ID3fake-audio-bytes"


def _enable_tts(ai_session, active=True, api_base="https://tts.example.com/v1"):
    """Seed the dedicated TTS provider row so /ai/tts finds it configured."""
    from cps.ai.routes import TTS_PROVIDER_NAME
    from cps.ai.crypto import encrypt_value
    from cps.ai.routes import _get_encryption_key
    row = ai_session.query(AiProvider).filter_by(
        provider_name=TTS_PROVIDER_NAME).first()
    if row is None:
        row = AiProvider()
        row.provider_name = TTS_PROVIDER_NAME
        ai_session.add(row)
    row.api_base = api_base
    row.api_key_encrypted = encrypt_value("sk-tts", _get_encryption_key())
    row.models_json = json.dumps({"model": "tts-1", "voice": "alloy"})
    row.active = active
    ai_session.commit()
    return row


class TestTtsRoute:
    def test_requires_login(self, client):
        rv = client.post("/ai/tts", json={"text": "hello"})
        assert rv.status_code == 302

    def test_rejects_empty_text(self, admin_client):
        rv = admin_client.post("/ai/tts", json={"text": "   "})
        assert rv.status_code == 400

    def test_rejects_oversized_text(self, admin_client):
        rv = admin_client.post("/ai/tts", json={"text": "x" * 2001})
        assert rv.status_code == 400

    def test_returns_503_when_not_configured(self, admin_client):
        rv = admin_client.post("/ai/tts", json={"text": "hello"})
        assert rv.status_code == 503
        assert "not configured" in rv.get_json()["error"]

    def test_returns_503_when_disabled(self, admin_client, ai_session):
        _enable_tts(ai_session, active=False)
        rv = admin_client.post("/ai/tts", json={"text": "hello"})
        assert rv.status_code == 503

    def test_synthesizes_audio(self, admin_client, ai_session):
        _enable_tts(ai_session)
        captured = {}

        fake = MagicMock()
        fake.status_code = 200
        fake.headers = {"Content-Type": "audio/mpeg"}
        fake.content = MP3

        def fake_post(url, headers=None, json=None, timeout=None):
            captured.update({"url": url, "headers": headers, "json": json})
            return fake

        with patch("cps.ai.tts.requests.post", side_effect=fake_post):
            rv = admin_client.post("/ai/tts", json={"text": "hello world"})
        assert rv.status_code == 200
        assert rv.mimetype == "audio/mpeg"
        assert rv.data == MP3
        assert captured["url"] == "https://tts.example.com/v1/audio/speech"
        assert captured["headers"]["Authorization"] == "Bearer sk-tts"
        assert captured["json"]["model"] == "tts-1"
        assert captured["json"]["voice"] == "alloy"
        assert captured["json"]["input"] == "hello world"
        assert captured["json"]["response_format"] == "mp3"

    def test_serves_second_request_from_cache(self, admin_client, ai_session):
        """Replaying the same paragraph must not hit the TTS API again."""
        _enable_tts(ai_session)

        fake = MagicMock()
        fake.status_code = 200
        fake.headers = {"Content-Type": "audio/mpeg"}
        fake.content = MP3

        with patch("cps.ai.tts.requests.post", return_value=fake) as post:
            for _ in range(2):
                rv = admin_client.post("/ai/tts", json={"text": "cached text"})
                assert rv.status_code == 200
                assert rv.data == MP3
        assert post.call_count == 1

    def test_returns_502_on_synthesis_error(self, admin_client, ai_session):
        _enable_tts(ai_session)
        fake = MagicMock()
        fake.status_code = 500
        fake.text = "upstream boom"

        with patch("cps.ai.tts.requests.post", return_value=fake):
            rv = admin_client.post("/ai/tts", json={"text": "hello"})
        assert rv.status_code == 502
        assert "500" in rv.get_json()["error"]


class TestTestTtsRoute:
    def test_rejects_non_http_base(self, admin_client):
        rv = admin_client.post("/ai/test_tts", json={"api_base": "ftp://x"})
        assert rv.status_code == 400

    def test_returns_audio_on_success(self, admin_client, ai_session):
        _enable_tts(ai_session)
        fake = MagicMock()
        fake.status_code = 200
        fake.headers = {"Content-Type": "audio/mpeg"}
        fake.content = MP3
        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured.update({"url": url, "json": json, "headers": headers})
            return fake

        with patch("cps.ai.tts.requests.post", side_effect=fake_post):
            rv = admin_client.post("/ai/test_tts", json={
                "api_base": "https://tts.example.com/v1",
                "api_key": "", "model": "tts-1", "voice": "alloy"})
        assert rv.status_code == 200
        assert rv.mimetype == "audio/mpeg"
        # blank api_key falls back to the stored key
        assert captured["headers"]["Authorization"] == "Bearer sk-tts"

    def test_returns_error_json_on_failure(self, admin_client, ai_session):
        _enable_tts(ai_session)
        fake = MagicMock()
        fake.status_code = 401
        fake.text = "bad key"

        with patch("cps.ai.tts.requests.post", return_value=fake):
            rv = admin_client.post("/ai/test_tts", json={
                "api_base": "https://tts.example.com/v1"})
        assert rv.status_code == 502
        assert "401" in rv.get_json()["error"]


class TestTtsAdmin:
    def test_admin_post_persists_tts_config(self, admin_client, ai_session):
        from cps.ai.routes import TTS_PROVIDER_NAME
        rv = admin_client.post("/ai/admin", data={
            "enabled": "on", "default_provider": "deepseek",
            "tts_enabled": "on", "tts_api_base": "https://gw.example.com/v1",
            "tts_api_key": "sk-new", "tts_model": "cosyvoice",
            "tts_voice": "nova",
        }, follow_redirects=True)
        assert rv.status_code == 200

        row = ai_session.query(AiProvider).filter_by(
            provider_name=TTS_PROVIDER_NAME).first()
        assert row is not None
        assert row.active is True
        assert row.api_base == "https://gw.example.com/v1"
        settings = json.loads(row.models_json)
        assert settings["model"] == "cosyvoice"
        assert settings["voice"] == "nova"

    def test_tts_row_excluded_from_generic_provider_loop(self, admin_client,
                                                         ai_session):
        """The tts row's {"model","voice"} models_json must survive a full
        admin form save (the generic provider loop would overwrite it with an
        id|label list)."""
        from cps.ai.routes import TTS_PROVIDER_NAME
        _enable_tts(ai_session)
        # A full generic form save including a bogus models textarea for tts
        row = ai_session.query(AiProvider).filter_by(
            provider_name=TTS_PROVIDER_NAME).first()
        row_id = row.id
        rv = admin_client.post("/ai/admin", data={
            "enabled": "on", "default_provider": "deepseek",
            "tts_enabled": "on", "tts_api_base": "https://gw.example.com/v1",
            f"provider_{row_id}_models": "should-be-ignored|ignored",
        }, follow_redirects=True)
        assert rv.status_code == 200

        ai_session.expire_all()
        row = ai_session.query(AiProvider).filter_by(
            provider_name=TTS_PROVIDER_NAME).first()
        settings = json.loads(row.models_json)
        assert settings["model"] == "tts-1"
        assert settings["voice"] == "alloy"


class TestTranslateBatchProxy:
    def test_requires_login(self, client):
        rv = client.post("/ajax/reading-translate-batch",
                         json={"paragraphs": ["hi"]})
        assert rv.status_code == 302

    def test_rejects_missing_paragraphs(self, admin_client):
        rv = admin_client.post("/ajax/reading-translate-batch", json={})
        assert rv.status_code == 400

    def test_rejects_too_many_paragraphs(self, admin_client):
        rv = admin_client.post("/ajax/reading-translate-batch",
                               json={"paragraphs": ["p"] * 21})
        assert rv.status_code == 400

    def test_rejects_oversized_paragraph(self, admin_client):
        rv = admin_client.post("/ajax/reading-translate-batch",
                               json={"paragraphs": ["x" * 2001]})
        assert rv.status_code == 400

    def test_rejects_blank_paragraph(self, admin_client):
        rv = admin_client.post("/ajax/reading-translate-batch",
                               json={"paragraphs": ["  "]})
        assert rv.status_code == 400

    def test_proxies_to_moonwell(self, admin_client, moonwell_configured,
                                  monkeypatch):
        import requests

        captured = {}

        class FakeResponse:
            status_code = 200
            text = json.dumps({"result": ["第一段", "第二段"]})
            headers = {"Content-Type": "application/json"}

        def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
            captured.update({"url": url, "json": json, "timeout": timeout})
            return FakeResponse()

        monkeypatch.setattr(requests, "post", fake_post)
        rv = admin_client.post("/ajax/reading-translate-batch",
                               json={"paragraphs": [" One. ", "Two."]},
                               headers={"authorization": "Bearer jwt"})
        assert rv.status_code == 200
        assert rv.get_json()["result"] == ["第一段", "第二段"]
        assert captured["url"].endswith("/vocabulary/reading/translate-batch")
        # paragraphs are trimmed before forwarding
        assert captured["json"]["paragraphs"] == ["One.", "Two."]
        # one LLM call for the whole page: generous timeout
        assert captured["timeout"] == 60

    def test_returns_503_when_upstream_unavailable(self, admin_client,
                                                   moonwell_configured,
                                                   monkeypatch):
        import requests

        def fake_post(url, json=None, headers=None, timeout=None, proxies=None):
            raise requests.RequestException("connection refused")

        monkeypatch.setattr(requests, "post", fake_post)
        rv = admin_client.post("/ajax/reading-translate-batch",
                               json={"paragraphs": ["hi"]},
                               headers={"authorization": "Bearer jwt"})
        assert rv.status_code == 503


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


class TestSynthesizeSpeech:
    def _post(self, status_code=200, content_type="audio/mpeg", content=MP3):
        fake = MagicMock()
        fake.status_code = status_code
        fake.headers = {"Content-Type": content_type}
        fake.content = content
        fake.text = content.decode("utf-8", "replace") if isinstance(content, bytes) else content
        return fake

    def test_success_returns_bytes(self):
        from cps.ai.tts import synthesize_speech
        with patch("cps.ai.tts.requests.post",
                   return_value=self._post()):
            assert synthesize_speech("https://x/v1/", "sk", "tts-1",
                                     "alloy", "hi") == MP3

    def test_error_status_raises(self):
        from cps.ai.tts import synthesize_speech
        with patch("cps.ai.tts.requests.post",
                   return_value=self._post(status_code=402)):
            with pytest.raises(RuntimeError, match="402"):
                synthesize_speech("https://x/v1", "sk", "tts-1", "a", "hi")

    def test_json_body_raises(self):
        """Some gateways answer 200 with a JSON error object instead of audio."""
        from cps.ai.tts import synthesize_speech
        with patch("cps.ai.tts.requests.post",
                   return_value=self._post(content_type="application/json",
                                           content=b'{"error":"quota"}')):
            with pytest.raises(RuntimeError, match="quota"):
                synthesize_speech("https://x/v1", "sk", "tts-1", "a", "hi")

    def test_empty_audio_raises(self):
        from cps.ai.tts import synthesize_speech
        with patch("cps.ai.tts.requests.post",
                   return_value=self._post(content=b"")):
            with pytest.raises(RuntimeError, match="empty"):
                synthesize_speech("https://x/v1", "sk", "tts-1", "a", "hi")

    def test_keyless_request_has_no_auth_header(self):
        from cps.ai.tts import synthesize_speech
        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["headers"] = headers
            return self._post()

        with patch("cps.ai.tts.requests.post", side_effect=fake_post):
            synthesize_speech("https://x/v1", "", "tts-1", "alloy", "hi")
        assert "Authorization" not in captured["headers"]


class TestLruCache:
    def test_put_get_and_eviction(self):
        from cps.ai.tts import LruCache
        cache = LruCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        assert cache.get("a") == 1
        assert cache.get("missing") is None
        cache.put("c", 3)  # evicts "b": a was just read, so b is least recently used
        assert cache.get("a") == 1
        assert cache.get("b") is None
        assert cache.get("c") == 3

    def test_tts_cache_key_covers_model_voice_text(self):
        from cps.ai.tts import tts_cache_key
        base = tts_cache_key("m", "v", "t")
        assert base == tts_cache_key("m", "v", "t")
        assert base != tts_cache_key("m2", "v", "t")
        assert base != tts_cache_key("m", "v2", "t")
        assert base != tts_cache_key("m", "v", "t2")
