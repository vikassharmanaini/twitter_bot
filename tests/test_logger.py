"""Tests for logger module."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.config_loader import AppConfig
from src.logger import JsonFormatter, log_with_metadata, setup_logging
from tests.fixtures import MINIMAL_CONFIG_DICT


def _cfg(overrides: dict | None = None) -> AppConfig:
    d = {**MINIMAL_CONFIG_DICT}
    if overrides:
        d = {**d, **overrides}
    return AppConfig.model_validate(d)


def test_setup_logging_creates_rotating_file(tmp_path: Path) -> None:
    log_file = tmp_path / "logs" / "t.log"
    cfg = _cfg({"logging": {**MINIMAL_CONFIG_DICT["logging"], "log_file": str(log_file)}})
    log = setup_logging(cfg, name="tlog")
    log.info("hello", extra={"metadata": {"tweet_id": "1"}})
    assert log_file.is_file()
    line = log_file.read_text(encoding="utf-8").strip().splitlines()[0]
    obj = json.loads(line)
    assert obj["level"] == "INFO"
    assert obj["message"] == "hello"
    assert obj["metadata"]["tweet_id"] == "1"


def test_json_formatter_redacts_sensitive_keys() -> None:
    fmt = JsonFormatter()
    rec = logging.LogRecord("n", logging.INFO, __file__, 1, "m", (), None)
    rec.metadata = {"api_key": "secret123", "tweet_id": "x"}  # type: ignore[attr-defined]
    s = fmt.format(rec)
    obj = json.loads(s)
    assert obj["metadata"]["api_key"] == "[REDACTED]"
    assert obj["metadata"]["tweet_id"] == "x"


def test_log_with_metadata(tmp_path: Path) -> None:
    log_path = tmp_path / "l.log"
    cfg = _cfg({"logging": {**MINIMAL_CONFIG_DICT["logging"], "log_file": str(log_path)}})
    log = setup_logging(cfg, name="lwmeta")
    log_with_metadata(log, logging.INFO, "x", bearer="tok")
    text = log_path.read_text(encoding="utf-8")
    assert '"message": "x"' in text
    assert "[REDACTED]" in text
