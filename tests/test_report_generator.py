"""Tests for report_generator."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.report_generator import write_report
from tests.fixtures import MINIMAL_CONFIG_DICT


def test_write_report(tmp_path: Path) -> None:
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {**MINIMAL_CONFIG_DICT["paths"], "knowledge_db": str(tmp_path / "r.db")}
    cfg = AppConfig.model_validate(d)
    store = KnowledgeStore(cfg)
    store.record_reply("x", "u", "text", datetime.now(timezone.utc), {})
    p = write_report(store, tmp_path / "rep.html")
    assert "Weekly" in p.read_text(encoding="utf-8")
    store.close()
