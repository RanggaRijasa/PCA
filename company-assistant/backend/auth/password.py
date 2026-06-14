"""Password hashing helpers using standard-library PBKDF2-HMAC-SHA256."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os


_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000
_SALT_BYTES = 16
_KEY_BYTES = 32


def hash_password(password: str) -> str:
    """Return a versioned salted password hash suitable for SQLite storage."""

    if len(password) < 12:
        raise ValueError("Passwords must contain at least 12 characters.")
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS, dklen=_KEY_BYTES
    )
    return "$".join(
        (
            _ALGORITHM,
            str(_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(derived).decode("ascii"),
        )
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify a password without leaking comparison timing information."""

    try:
        algorithm, iterations, salt_value, expected_value = encoded_hash.split("$", 3)
        if algorithm != _ALGORITHM:
            return False
        salt = base64.urlsafe_b64decode(salt_value.encode("ascii"))
        expected = base64.urlsafe_b64decode(expected_value.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)
