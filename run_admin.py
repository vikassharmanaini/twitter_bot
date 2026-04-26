#!/usr/bin/env python3
"""Run the local admin API + WebSocket (bind 127.0.0.1 by default)."""

from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    host = os.environ.get("ADMIN_BIND", "127.0.0.1")
    port = int(os.environ.get("ADMIN_PORT", "8080"))
    uvicorn.run(
        "src.admin.api.main:app",
        host=host,
        port=port,
        reload=os.environ.get("ADMIN_RELOAD", "").lower() in ("1", "true", "yes"),
    )
