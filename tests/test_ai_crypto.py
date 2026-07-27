"""Tests for AI config value encryption helpers."""
from cryptography.fernet import Fernet

from cps.ai.crypto import encrypt_value, decrypt_value


class TestCrypto:
    def test_roundtrip_string(self):
        key = Fernet.generate_key()  # valid 32-byte url-safe base64 Fernet key
        original = "sk-deepseek-abc123"
        encrypted = encrypt_value(original, key)
        assert encrypted != original
        assert decrypt_value(encrypted, key) == original

    def test_decrypt_invalid_returns_empty(self):
        key = Fernet.generate_key()
        assert decrypt_value("not-a-valid-token", key) == ""

    def test_encrypt_empty_returns_empty(self):
        key = Fernet.generate_key()
        assert encrypt_value("", key) == ""
        assert encrypt_value(None, key) == ""
