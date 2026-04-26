"""
config_loader.py

Loads and validates config.yaml (and optional .env). Fails with explicit missing-key errors.
Key dependencies: PyYAML, pydantic, pathlib, os
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

HUMOR_LEVELS = frozenset({"low", "medium", "high"})
SEARCH_PROVIDERS = frozenset({"duckduckgo", "serper", "brave"})
LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"})


class OpenRouterConfig(BaseModel):
    api_key: str
    primary_model: str
    fallback_model: str
    max_tokens_per_run: int = 5000


class TwitterConfig(BaseModel):
    bearer_token: str
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str


class BotConfigSection(BaseModel):
    schedule_interval_minutes: int = 45
    schedule_jitter_percent: int = 20
    max_replies_per_day: int = 20
    accounts_per_cycle: int = 3
    min_tweet_age_minutes: int = 5
    max_tweet_age_hours: int = 24
    humor_level: Literal["low", "medium", "high"] = "medium"
    dry_run: bool = False
    min_target_followers: int = 10_000


class SearchConfig(BaseModel):
    provider: Literal["duckduckgo", "serper", "brave"] = "duckduckgo"
    serper_api_key: str = ""
    brave_api_key: str = ""
    cache_ttl_minutes: int = 30


class SafetyConfig(BaseModel):
    daily_reply_cap: int = 20
    min_minutes_between_posts: int = 20
    blacklisted_words: list[str] = Field(default_factory=list)
    max_similarity_to_recent: float = 0.70
    tragedy_keywords: list[str] = Field(default_factory=list)


class LoggingConfig(BaseModel):
    level: str = "INFO"
    log_file: str = "logs/bot.log"
    max_log_size_mb: int = 10
    backup_count: int = 5

    @field_validator("level")
    @classmethod
    def level_ok(cls, v: str) -> str:
        u = v.upper()
        if u == "WARN":
            u = "WARNING"
        if u not in LOG_LEVELS:
            raise ValueError(f"logging.level must be one of {sorted(LOG_LEVELS)}, got {v!r}")
        return u


class PathsConfig(BaseModel):
    targets_file: str = "data/targets.yaml"
    bot_state_file: str = "data/bot_state.json"
    knowledge_db: str = "data/bot.db"
    target_cache_file: str = "data/target_cache.json"


class AppConfig(BaseModel):
    openrouter: OpenRouterConfig
    twitter: TwitterConfig
    bot: BotConfigSection = Field(default_factory=BotConfigSection)
    search: SearchConfig = Field(default_factory=SearchConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)


def _is_placeholder(s: str) -> bool:
    t = (s or "").strip()
    return not t or t.startswith("REPLACE_ME") or t == "sk-or-REPLACE_ME"


def _validate_secrets(cfg: AppConfig) -> None:
    if _is_placeholder(cfg.openrouter.api_key):
        raise ValueError(
            "config error: openrouter.api_key is missing or still a placeholder; set a real key in config.yaml"
        )
    tw = cfg.twitter
    for name, val in [
        ("twitter.bearer_token", tw.bearer_token),
        ("twitter.api_key", tw.api_key),
        ("twitter.api_secret", tw.api_secret),
        ("twitter.access_token", tw.access_token),
        ("twitter.access_token_secret", tw.access_token_secret),
    ]:
        if _is_placeholder(val):
            raise ValueError(f"config error: {name} is missing or still a placeholder")


def load_raw_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"config must be a YAML mapping at top level, got {type(data).__name__}")
    return data


def merge_defaults(raw: dict[str, Any]) -> dict[str, Any]:
    """Ensure nested dicts exist for pydantic defaults."""
    out = dict(raw)
    out.setdefault("bot", {})
    out.setdefault("search", {})
    out.setdefault("safety", {})
    out.setdefault("logging", {})
    out.setdefault("paths", {})
    return out


def load_config(
    config_path: str | Path | None = None,
    *,
    skip_secret_validation: bool = False,
) -> AppConfig:
    """
    Load application config from config.yaml (or given path).
    Loads .env from cwd if present (does not override existing env vars by default).
    """
    load_dotenv(override=False)
    path = Path(config_path or os.environ.get("BOT_CONFIG", "config.yaml"))
    raw = merge_defaults(load_raw_yaml(path))
    try:
        cfg = AppConfig.model_validate(raw)
    except Exception as e:
        raise ValueError(f"config validation failed: {e}") from e
    if cfg.search.provider == "serper" and _is_placeholder(cfg.search.serper_api_key):
        raise ValueError("config error: search.provider is serper but search.serper_api_key is missing")
    if cfg.search.provider == "brave" and _is_placeholder(cfg.search.brave_api_key):
        raise ValueError("config error: search.provider is brave but search.brave_api_key is missing")
    if not skip_secret_validation:
        _validate_secrets(cfg)
    return cfg
