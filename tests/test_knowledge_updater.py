"""Tests for knowledge_updater."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.knowledge_updater import KnowledgeUpdater
from src.models import SearchContext, SearchResultItem
from src.web_searcher import WebSearcher
from tests.fixtures import MINIMAL_CONFIG_DICT


def test_knowledge_updater_adds_snippets(tmp_path: Path) -> None:
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {**MINIMAL_CONFIG_DICT["paths"], "knowledge_db": str(tmp_path / "ku.db")}
    cfg = AppConfig.model_validate(d)
    store = KnowledgeStore(cfg)
    for _ in range(5):
        store.bump_topic("AI")

    llm = MagicMock()
    llm.chat.return_value = "summary paragraph"
    searcher = MagicMock(spec=WebSearcher)
    searcher.search.return_value = SearchContext(
        query="q",
        results=[SearchResultItem(title="t", url="http://x", snippet="s")],
        summary="x",
    )
    ku = KnowledgeUpdater(cfg, store, llm, searcher)
    n = ku.run_daily()
    assert n >= 1
    store.close()
