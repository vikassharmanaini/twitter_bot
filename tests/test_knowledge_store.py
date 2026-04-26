"""Tests for knowledge_store."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from tests.fixtures import MINIMAL_CONFIG_DICT


def _store(tmp_path: Path) -> KnowledgeStore:
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {**MINIMAL_CONFIG_DICT["paths"], "knowledge_db": str(tmp_path / "t.db")}
    cfg = AppConfig.model_validate(d)
    return KnowledgeStore(cfg)


def test_record_and_has_replied(tmp_path: Path) -> None:
    ks = _store(tmp_path)
    assert not ks.has_replied_to("1")
    ks.record_reply(
        "1",
        "acc",
        "hi",
        datetime.now(timezone.utc),
        {"x": 1},
    )
    assert ks.has_replied_to("1")
    ks.close()


def test_daily_reply_count(tmp_path: Path) -> None:
    ks = _store(tmp_path)
    assert ks.get_daily_reply_count() == 0
    ks.increment_daily_replies(2)
    assert ks.get_daily_reply_count() == 2
    ks.close()


def test_recent_reply_texts(tmp_path: Path) -> None:
    ks = _store(tmp_path)
    ks.record_reply("a", "u", "one", datetime.now(timezone.utc), {})
    ks.record_reply("b", "u", "two", datetime.now(timezone.utc), {})
    r = ks.recent_reply_texts(limit=5)
    assert r[0] == "two"
    ks.close()


def test_clear_history(tmp_path: Path) -> None:
    ks = _store(tmp_path)
    ks.record_reply("x", "u", "t", datetime.now(timezone.utc), {})
    ks.clear_replied_history()
    assert not ks.has_replied_to("x")
    ks.close()
