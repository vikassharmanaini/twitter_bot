"""
Shared test data: sample configs, tweets, LLM responses.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.models import Tweet

MINIMAL_CONFIG_DICT: dict[str, Any] = {
    "openrouter": {
        "api_key": "sk-or-test-key-12345",
        "primary_model": "test/model-a",
        "fallback_model": "test/model-b",
        "max_tokens_per_run": 1000,
    },
    "twitter": {
        "bearer_token": "bearer-test-token",
        "api_key": "ck",
        "api_secret": "cs",
        "access_token": "atk",
        "access_token_secret": "ats",
    },
    "bot": {
        "schedule_interval_minutes": 45,
        "schedule_jitter_percent": 20,
        "max_replies_per_day": 20,
        "accounts_per_cycle": 3,
        "min_tweet_age_minutes": 5,
        "max_tweet_age_hours": 24,
        "humor_level": "medium",
        "dry_run": True,
        "min_target_followers": 10000,
    },
    "search": {"provider": "duckduckgo", "serper_api_key": "", "brave_api_key": "", "cache_ttl_minutes": 30},
    "safety": {
        "daily_reply_cap": 20,
        "min_minutes_between_posts": 20,
        "blacklisted_words": [],
        "max_similarity_to_recent": 0.7,
        "tragedy_keywords": ["death"],
    },
    "logging": {
        "level": "INFO",
        "log_file": "logs/test_bot.log",
        "max_log_size_mb": 1,
        "backup_count": 2,
    },
    "paths": {
        "targets_file": "data/targets.yaml",
        "bot_state_file": "data/bot_state.json",
        "knowledge_db": "data/test_bot.db",
        "target_cache_file": "data/test_target_cache.json",
    },
}


def write_config_yaml(path: Path, overrides: dict[str, Any] | None = None) -> Path:
    data = deepcopy(MINIMAL_CONFIG_DICT)
    if overrides:
        for k, v in overrides.items():
            if isinstance(v, dict) and k in data and isinstance(data[k], dict):
                data[k] = {**data[k], **v}
            else:
                data[k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)
    return path


SAMPLE_TWEET = Tweet(
    tweet_id="123",
    author_username="dev",
    author_id="42",
    text="Rust 1.75 is out!",
    created_at=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
    like_count=100,
    retweet_count=20,
    reply_count=5,
    is_retweet=False,
    is_reply=False,
)
