"""Tests for safety_filter."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import pytest

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.models import SafetyDecision
from src.safety_filter import SafetyFilter
from tests.fixtures import MINIMAL_CONFIG_DICT


def _sf(tmp_path: Path, **kwargs) -> tuple[SafetyFilter, KnowledgeStore]:
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {**MINIMAL_CONFIG_DICT["paths"], "knowledge_db": str(tmp_path / "s.db")}
    cfg = AppConfig.model_validate(d)
    store = KnowledgeStore(cfg)
    llm = kwargs.get("llm")
    return SafetyFilter(cfg, store, llm=llm, logger=None), store


@pytest.fixture
def safety_pair(tmp_path: Path) -> tuple[SafetyFilter, KnowledgeStore]:
    sf, store = _sf(tmp_path)
    yield sf, store
    store.close()


def test_safety_rejects_long(safety_pair: tuple[SafetyFilter, KnowledgeStore]) -> None:
    sf, _ = safety_pair
    r = sf.evaluate("1", "a", "x" * 300)
    assert r.decision == SafetyDecision.REJECTED_WITH_REASON


def test_safety_rejects_duplicate(safety_pair: tuple[SafetyFilter, KnowledgeStore]) -> None:
    sf, store = safety_pair
    store.record_reply("1", "a", "x", datetime.now(timezone.utc), {})
    r = sf.evaluate("1", "a", "short")
    assert "already" in r.reason


def test_safety_blacklist(tmp_path: Path) -> None:
    d = {**MINIMAL_CONFIG_DICT}
    d["safety"] = {**MINIMAL_CONFIG_DICT["safety"], "blacklisted_words": ["badword"]}
    d["paths"] = {**MINIMAL_CONFIG_DICT["paths"], "knowledge_db": str(tmp_path / "b.db")}
    cfg = AppConfig.model_validate(d)
    store = KnowledgeStore(cfg)
    try:
        sf = SafetyFilter(cfg, store, llm=None)
        r = sf.evaluate("9", "a", "this has badword inside")
        assert r.decision == SafetyDecision.REJECTED_WITH_REASON
    finally:
        store.close()


def test_safety_approve_with_skip_llm(safety_pair: tuple[SafetyFilter, KnowledgeStore]) -> None:
    sf, _ = safety_pair
    r = sf.evaluate("99", "acc", "nice reply here", skip_bot_llm=True)
    assert r.decision == SafetyDecision.APPROVED


def test_safety_tragedy_keyword(safety_pair: tuple[SafetyFilter, KnowledgeStore]) -> None:
    sf, _ = safety_pair
    r = sf.evaluate("9", "a", "ok", tweet_text="discussing death and loss today", skip_bot_llm=True)
    assert r.decision == SafetyDecision.REJECTED_WITH_REASON


def test_safety_low_followers(safety_pair: tuple[SafetyFilter, KnowledgeStore]) -> None:
    sf, _ = safety_pair
    r = sf.evaluate("1", "a", "hi", author_followers=100, skip_bot_llm=True)
    assert r.decision == SafetyDecision.REJECTED_WITH_REASON


def test_safety_similarity(safety_pair: tuple[SafetyFilter, KnowledgeStore]) -> None:
    sf, store = safety_pair
    store.record_reply("x", "u", "hello world reply", datetime.now(timezone.utc), {})
    r = sf.evaluate("2", "a", "hello world reply", skip_bot_llm=True)
    assert r.decision == SafetyDecision.REJECTED_WITH_REASON


def test_safety_cooldown(safety_pair: tuple[SafetyFilter, KnowledgeStore]) -> None:
    sf, store = safety_pair
    store.record_reply("p", "u", "old", datetime.now(timezone.utc), {})
    r = sf.evaluate("3", "a", "new reply text here", skip_bot_llm=True)
    assert r.decision == SafetyDecision.REJECTED_WITH_REASON
