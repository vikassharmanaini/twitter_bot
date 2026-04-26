"""
Thread-safe log queue + logging.Handler that pushes redacted JSON lines for WebSocket fan-out.
"""

from __future__ import annotations

import json
import logging
import queue
from typing import Any

from src.logger import JsonFormatter


class LogBroadcaster:
    """Fan-out queue consumed by the async WebSocket loop."""

    def __init__(self, maxsize: int = 2000) -> None:
        self._q: queue.Queue[str] = queue.Queue(maxsize=maxsize)

    def put_log_line(self, line: str) -> None:
        try:
            self._q.put_nowait(line)
        except queue.Full:
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            try:
                self._q.put_nowait(line)
            except queue.Full:
                pass

    def get_nowait_batch(self, max_items: int = 50) -> list[str]:
        out: list[str] = []
        for _ in range(max_items):
            try:
                out.append(self._q.get_nowait())
            except queue.Empty:
                break
        return out


class BroadcastLogHandler(logging.Handler):
    """Attach to twitter_bot logger; forwards JsonFormatter output to LogBroadcaster."""

    def __init__(self, broadcaster: LogBroadcaster) -> None:
        super().__init__()
        self._broadcaster = broadcaster
        self.setFormatter(JsonFormatter())

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._broadcaster.put_log_line(msg)
        except Exception:
            self.handleError(record)


def parse_log_line_for_event(line: str) -> dict[str, Any]:
    """Parse JSON log line into a WS event payload."""
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return {"type": "log", "raw": line, "level": "INFO", "message": line}
