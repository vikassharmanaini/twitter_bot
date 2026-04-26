"""Pytest fixtures: reset admin BotRuntimeService singleton between tests."""

from __future__ import annotations

import pytest

from src.admin.application.bot_runtime import BotRuntimeService


@pytest.fixture(autouse=True)
def reset_bot_runtime_singleton() -> None:
    inst = BotRuntimeService._instance
    if inst is not None:
        try:
            inst.stop()
        except Exception:
            pass
    BotRuntimeService._instance = None
    yield
    inst = BotRuntimeService._instance
    if inst is not None:
        try:
            inst.stop()
        except Exception:
            pass
    BotRuntimeService._instance = None
