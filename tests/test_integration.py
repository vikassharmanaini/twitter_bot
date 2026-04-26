"""Integration test: dry-run cycle with mocks."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import yaml

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.main_loop import MainLoop
from src.models import Tweet
from src.twitter_client import TwitterClient
from tests.fixtures import MINIMAL_CONFIG_DICT


def test_full_loop_dry_run_integration(tmp_path: Path) -> None:
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {
        **MINIMAL_CONFIG_DICT["paths"],
        "knowledge_db": str(tmp_path / "int.db"),
        "targets_file": str(tmp_path / "targets.yaml"),
        "target_cache_file": str(tmp_path / "cache.json"),
    }
    d["bot"] = {**MINIMAL_CONFIG_DICT["bot"], "dry_run": True, "accounts_per_cycle": 1}
    cfg = AppConfig.model_validate(d)
    (tmp_path / "targets.yaml").write_text(
        yaml.safe_dump({"targets": [{"username": "techgiant", "priority": 1, "enabled": True}]}),
        encoding="utf-8",
    )
    store = KnowledgeStore(cfg)
    twitter = MagicMock(spec=TwitterClient)
    twitter.get_user_profile.return_value = ("u1", 100_000)
    twitter.get_recent_tweets.return_value = [
        Tweet(
            tweet_id="int1",
            author_username="techgiant",
            author_id="u1",
            text="We shipped a new API today.",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            like_count=50,
            retweet_count=10,
            is_retweet=False,
            is_reply=False,
        )
    ]
    twitter.has_already_replied.return_value = False

    llm = MagicMock()
    llm.reset_budget = MagicMock()
    llm.usage_summary = {"prompt_tokens": 0, "completion_tokens": 0, "budget_remaining": 9999}
    llm.chat.side_effect = [
        '{"topic":"API","sentiment":"positive","tweet_type":"announcement","technical_level":"intermediate",'
        '"key_entities":["API"],"requires_web_search":false,"search_query":null}',
        "nice\n---\nwow\n---\ncool",
        '[{"human_likeness":8,"relevance":9,"engagement_potential":8,"risk_score":2},'
        '{"human_likeness":7,"relevance":8,"engagement_potential":7,"risk_score":3},'
        '{"human_likeness":6,"relevance":7,"engagement_potential":6,"risk_score":4}]',
        "NO",
    ]

    loop = MainLoop(cfg, twitter=twitter, store=store, llm=llm)
    summary = loop.run_cycle()
    assert summary["posted"] == 0
    assert any("dry-run" in m or "would" in m for m in summary.get("messages", []))
    store.close()
