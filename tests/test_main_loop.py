"""Tests for main_loop."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.main_loop import MainLoop
from src.models import Tweet
from src.twitter_client import TwitterClient
from tests.fixtures import MINIMAL_CONFIG_DICT


def _loop_mocks(tmp_path: Path) -> MainLoop:
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {
        **MINIMAL_CONFIG_DICT["paths"],
        "knowledge_db": str(tmp_path / "m.db"),
        "targets_file": str(tmp_path / "targets.yaml"),
        "target_cache_file": str(tmp_path / "cache.json"),
    }
    d["bot"] = {**MINIMAL_CONFIG_DICT["bot"], "dry_run": True}
    cfg = AppConfig.model_validate(d)
    store = KnowledgeStore(cfg)
    twitter = MagicMock(spec=TwitterClient)
    twitter.get_user_profile.return_value = ("uid1", 50_000)
    tw = Tweet(
        tweet_id="t1",
        author_username="x",
        author_id="uid1",
        text="Hello world AI news today",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        like_count=10,
        retweet_count=2,
        is_retweet=False,
        is_reply=False,
    )
    twitter.get_recent_tweets.return_value = [tw]
    twitter.has_already_replied.return_value = False
    llm = MagicMock()
    llm.chat.side_effect = [
        '{"topic":"AI","sentiment":"neutral","tweet_type":"opinion","technical_level":"intermediate",'
        '"key_entities":["AI"],"requires_web_search":false,"search_query":null}',
        "a\n---\nb\n---\nc",
        '[{"human_likeness":8,"relevance":8,"engagement_potential":8,"risk_score":2},'
        '{"human_likeness":7,"relevance":7,"engagement_potential":7,"risk_score":3},'
        '{"human_likeness":6,"relevance":6,"engagement_potential":6,"risk_score":4}]',
        "NO",
    ]
    llm.reset_budget = MagicMock()
    llm.usage_summary = {"prompt_tokens": 1, "completion_tokens": 1, "budget_remaining": 100}

    loop = MainLoop(cfg, twitter=twitter, store=store, llm=llm)
    return loop


def test_run_cycle_regenerate_path(tmp_path: Path) -> None:
    import yaml

    tfile = tmp_path / "targets.yaml"
    tfile.write_text(
        yaml.safe_dump({"targets": [{"username": "bigaccount", "priority": 1, "enabled": True}]}),
        encoding="utf-8",
    )
    loop = _loop_mocks(tmp_path)
    loop._llm.chat.side_effect = [
        '{"topic":"AI","sentiment":"neutral","tweet_type":"opinion","technical_level":"intermediate",'
        '"key_entities":["AI"],"requires_web_search":false,"search_query":null}',
        "a\n---\nb\n---\nc",
        '[{"human_likeness":8,"relevance":8,"engagement_potential":8,"risk_score":2},'
        '{"human_likeness":7,"relevance":7,"engagement_potential":7,"risk_score":3},'
        '{"human_likeness":6,"relevance":6,"engagement_potential":6,"risk_score":4}]',
        "YES",
        "d\n---\ne\n---\nf",
        '[{"human_likeness":8,"relevance":8,"engagement_potential":8,"risk_score":2},'
        '{"human_likeness":7,"relevance":7,"engagement_potential":7,"risk_score":3},'
        '{"human_likeness":6,"relevance":6,"engagement_potential":6,"risk_score":4}]',
    ]
    summary = loop.run_cycle()
    assert summary["errors"] == 0
    loop._store.close()


def test_run_cycle_dry_run_smoke(tmp_path: Path) -> None:
    import yaml

    tfile = tmp_path / "targets.yaml"
    tfile.write_text(
        yaml.safe_dump({"targets": [{"username": "bigaccount", "priority": 1, "enabled": True}]}),
        encoding="utf-8",
    )
    loop = _loop_mocks(tmp_path)
    summary = loop.run_cycle()
    assert summary["accounts"] >= 1
    loop._store.close()


@patch("src.main_loop.time.sleep", return_value=None)
def test_run_cycle_posts_when_not_dry_run(_mock_sleep: MagicMock, tmp_path: Path) -> None:
    import yaml

    tfile = tmp_path / "targets.yaml"
    tfile.write_text(
        yaml.safe_dump({"targets": [{"username": "bigaccount", "priority": 1, "enabled": True}]}),
        encoding="utf-8",
    )
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {
        **MINIMAL_CONFIG_DICT["paths"],
        "knowledge_db": str(tmp_path / "m2.db"),
        "targets_file": str(tmp_path / "targets.yaml"),
        "target_cache_file": str(tmp_path / "cache2.json"),
    }
    d["bot"] = {**MINIMAL_CONFIG_DICT["bot"], "dry_run": False}
    cfg = AppConfig.model_validate(d)
    store = KnowledgeStore(cfg)
    try:
        twitter = MagicMock(spec=TwitterClient)
        twitter.get_user_profile.return_value = ("uid1", 50_000)
        tw = Tweet(
            tweet_id="t2",
            author_username="x",
            author_id="uid1",
            text="Hello world AI news today",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            like_count=10,
            retweet_count=2,
            is_retweet=False,
            is_reply=False,
        )
        twitter.get_recent_tweets.return_value = [tw]
        twitter.has_already_replied.return_value = False
        twitter.post_reply.return_value = "newid"

        llm = MagicMock()
        llm.reset_budget = MagicMock()
        llm.usage_summary = {"prompt_tokens": 1, "completion_tokens": 1, "budget_remaining": 100}
        llm.chat.side_effect = [
            '{"topic":"AI","sentiment":"neutral","tweet_type":"opinion","technical_level":"intermediate",'
            '"key_entities":["AI"],"requires_web_search":false,"search_query":null}',
            "a\n---\nb\n---\nc",
            '[{"human_likeness":8,"relevance":8,"engagement_potential":8,"risk_score":2},'
            '{"human_likeness":7,"relevance":7,"engagement_potential":7,"risk_score":3},'
            '{"human_likeness":6,"relevance":6,"engagement_potential":6,"risk_score":4}]',
            "NO",
        ]
        loop = MainLoop(cfg, twitter=twitter, store=store, llm=llm)
        summary = loop.run_cycle()
        assert summary["posted"] == 1
        twitter.post_reply.assert_called_once()
    finally:
        store.close()
