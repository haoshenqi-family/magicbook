"""Encryption helpers for storing sensitive AI config values (API keys) at rest.

Uses Fernet symmetric encryption from the `cryptography` package, which is
already a calibre-web dependency. The encryption key is the same one calibre-web
generates for its own config secrets (see cps.config_sql.get_encryption_key).
"""
from cryptography.fernet import Fernet, InvalidToken


def encrypt_value(value, key):
    """Encrypt a string with the given 32-byte url-safe base64 Fernet key.

    Returns an empty string if value is falsy (no point encrypting empty).
    """
    if not value:
        return ""
    try:
        f = Fernet(key)
        return f.encrypt(value.encode("utf-8")).decode("utf-8")
    except Exception:
        # If encryption fails, return empty rather than crashing the app
        return ""


def decrypt_value(token, key):
    """Decrypt a Fernet token back to the original string.

    Returns empty string if the token is invalid or decryption fails.
    """
    if not token or not key:
        return ""
    try:
        f = Fernet(key)
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        return ""
