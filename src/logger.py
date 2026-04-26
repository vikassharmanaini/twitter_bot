"""
logger.py

Structured JSON logging to console and rotating file; redacts secrets from log records.
Key dependencies: logging, logging.handlers, config_loader.AppConfig
"""

from __future__ import annotations

import json
import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from src.config_loader import AppConfig

_REDACT_KEYS = re.compile(
    r"(api_key|api_secret|bearer|token|secret|password|authorization)",
    re.I,
)


def _redact_value(key: str, value: Any) -> Any:
    if value is None:
        return None
    if _REDACT_KEYS.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: _redact_value(str(k), v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value("item", v) for v in value]
    if isinstance(value, str) and len(value) > 12 and _REDACT_KEYS.search(value):
        return "[REDACTED]"
    return value


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        extra = getattr(record, "metadata", None)
        if isinstance(extra, dict):
            payload["metadata"] = {k: _redact_value(str(k), v) for k, v in extra.items()}
        return json.dumps(payload, default=str)


def setup_logging(cfg: AppConfig, name: str = "twitter_bot") -> logging.Logger:
    """
    Configure root logger for the bot: console + rotating file from cfg.logging.
    """
    log = logging.getLogger(name)
    log.handlers.clear()
    lvl_name = cfg.logging.level.upper()
    if lvl_name == "WARN":
        lvl_name = "WARNING"
    log.setLevel(getattr(logging, lvl_name, logging.INFO))
    log.propagate = False

    console = logging.StreamHandler()
    console.setFormatter(JsonFormatter())
    log.addHandler(console)

    log_path = Path(cfg.logging.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    max_bytes = max(1, cfg.logging.max_log_size_mb) * 1024 * 1024
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=max(1, cfg.logging.backup_count),
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter())
    log.addHandler(file_handler)
    return log


def log_with_metadata(logger: logging.Logger, level: int, message: str, **metadata: Any) -> None:
    """Log with extra metadata dict (values redacted in JSON formatter)."""
    logger.log(level, message, extra={"metadata": metadata})
