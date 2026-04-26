"""
Runtime state for the bot worker thread (admin domain).
"""

from __future__ import annotations

from enum import Enum


class RuntimeState(str, Enum):
    stopped = "stopped"
    starting = "starting"
    running = "running"
    stopping = "stopping"
