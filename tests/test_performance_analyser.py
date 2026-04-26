"""Tests for performance_analyser."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.performance_analyser import PerformanceAnalyser
from src.twitter_client import TwitterClient
from tests.fixtures import MINIMAL_CONFIG_DICT


def test_performance_writes_file(tmp_path: Path) -> None:
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {**MINIMAL_CONFIG_DICT["paths"], "knowledge_db": str(tmp_path / "p.db")}
    cfg = AppConfig.model_validate(d)
    store = KnowledgeStore(cfg)
    store.record_reply("tid1", "a", "hello", datetime.now(timezone.utc), {})
    tw = MagicMock(spec=TwitterClient)
    tw.get_tweet_public_metrics.return_value = {"like_count": 3}
    llm = MagicMock()
    llm.chat.return_value = "## Insights\n- be concise\n"
    try:
        pa = PerformanceAnalyser(cfg, store, tw, llm, output_path=tmp_path / "perf.md")
        out = pa.run_weekly()
        assert out.is_file()
    finally:
        store.close()
