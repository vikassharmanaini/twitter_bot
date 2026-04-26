"""
Shared FastAPI dependencies (optional ADMIN_TOKEN).
"""

from __future__ import annotations

import os

from fastapi import Header, HTTPException, WebSocket


def require_admin_token(authorization: str | None = Header(None, alias="Authorization")) -> None:
    expected = os.environ.get("ADMIN_TOKEN", "").strip()
    if not expected:
        return
    if not authorization or authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def ws_token_ok(websocket: WebSocket) -> bool:
    expected = os.environ.get("ADMIN_TOKEN", "").strip()
    if not expected:
        return True
    q = websocket.query_params.get("token", "")
    if q == expected:
        return True
    # Allow Authorization header on WS (some clients)
    auth = websocket.headers.get("authorization", "")
    return auth == f"Bearer {expected}"
