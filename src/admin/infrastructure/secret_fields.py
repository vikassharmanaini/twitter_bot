"""
Detect which YAML/config keys should be treated as secrets in the admin API.
"""

from __future__ import annotations


def is_secret_key(name: str) -> bool:
    n = (name or "").lower()
    if n in {"api_key", "serper_api_key", "brave_api_key"}:
        return True
    if n.endswith("_secret") or n.endswith("_token") or "bearer" in n or "password" in n:
        return True
    return False


def is_probably_secret_path(path: str) -> bool:
    """Path like 'openrouter.api_key'."""
    parts = path.split(".")
    return bool(parts) and is_secret_key(parts[-1])
