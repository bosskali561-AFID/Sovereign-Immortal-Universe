"""Payload hygiene: recursively redact secret-looking keys."""
from __future__ import annotations

_SECRET_MARKERS = ("password", "secret", "token", "api_key", "apikey", "private_key", "authorization", "credential")


def clean_payload(payload: dict) -> dict:
    def _clean(value):
        if isinstance(value, dict):
            return {
                k: (
                    "[REDACTED]"
                    if any(marker in k.lower() for marker in _SECRET_MARKERS)
                    else _clean(v)
                )
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [_clean(v) for v in value]
        return value

    return _clean(payload or {})
