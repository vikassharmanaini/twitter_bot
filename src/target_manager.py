"""
target_manager.py

Loads target accounts from YAML, orders by priority and last-checked, caches user IDs.
Key dependencies: PyYAML, pathlib, twitter_client (optional resolve), config_loader
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.config_loader import AppConfig
from src.twitter_client import TwitterClient


@dataclass
class TargetAccount:
    username: str
    category: str = ""
    priority: int = 3
    enabled: bool = True
    last_checked_at: datetime | None = None
    user_id: str | None = None


def _parse_targets_doc(raw: dict[str, Any]) -> list[TargetAccount]:
    items = raw.get("targets") or raw.get("accounts")
    if not isinstance(items, list):
        raise ValueError("targets.yaml must contain a list under 'targets'")
    out: list[TargetAccount] = []
    for row in items:
        if not isinstance(row, dict):
            continue
        un = str(row.get("username", "")).lstrip("@").strip()
        if not un:
            continue
        lc = row.get("last_checked_at")
        last: datetime | None = None
        if isinstance(lc, str) and lc:
            try:
                last = datetime.fromisoformat(lc.replace("Z", "+00:00"))
            except ValueError:
                last = None
        out.append(
            TargetAccount(
                username=un,
                category=str(row.get("category", "")),
                priority=int(row.get("priority", 3)),
                enabled=bool(row.get("enabled", True)),
                last_checked_at=last,
                user_id=row.get("user_id"),
            )
        )
    return out


class TargetManager:
    def __init__(
        self,
        cfg: AppConfig,
        twitter: TwitterClient | None = None,
        logger: logging.Logger | None = None,
    ):
        self._cfg = cfg
        self._twitter = twitter
        self._log = logger or logging.getLogger("twitter_bot")
        self._targets_path = Path(cfg.paths.targets_file)
        self._cache_path = Path(cfg.paths.target_cache_file)

    def load_targets(self) -> list[TargetAccount]:
        if not self._targets_path.is_file():
            raise FileNotFoundError(f"targets file not found: {self._targets_path}")
        with self._targets_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            raise ValueError("targets.yaml must be a mapping at top level")
        accounts = _parse_targets_doc(raw)
        cache = self._load_cache()
        for a in accounts:
            cid = cache.get(a.username.lower())
            if cid and not a.user_id:
                a.user_id = cid
        return [a for a in accounts if a.enabled]

    def _load_cache(self) -> dict[str, str]:
        if not self._cache_path.is_file():
            return {}
        try:
            with self._cache_path.open(encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {str(k).lower(): str(v) for k, v in data.items()}
        except (json.JSONDecodeError, OSError):
            pass
        return {}

    def _save_cache(self, mapping: dict[str, str]) -> None:
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self._cache_path.open("w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2, sort_keys=True)

    def resolve_user_id(self, account: TargetAccount) -> str:
        if account.user_id:
            return account.user_id
        if not self._twitter:
            raise RuntimeError("TwitterClient required to resolve user_id")
        uid = self._twitter.get_user_id(account.username)
        account.user_id = uid
        cache = self._load_cache()
        cache[account.username.lower()] = uid
        self._save_cache(cache)
        return uid

    def get_accounts_to_check(self, limit: int | None = None) -> list[TargetAccount]:
        """
        Return enabled targets sorted by priority (1 first), then oldest last_checked.
        """
        accounts = self.load_targets()
        accounts.sort(
            key=lambda a: (
                a.priority,
                a.last_checked_at or datetime.min.replace(tzinfo=timezone.utc),
            )
        )
        if limit is not None:
            return accounts[: max(0, limit)]
        return accounts

    def mark_checked(self, username: str, when: datetime | None = None) -> None:
        """Update last_checked_at in targets file for username."""
        when = when or datetime.now(timezone.utc)
        if not self._targets_path.is_file():
            return
        with self._targets_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            return
        items = raw.get("targets") or []
        h = username.lstrip("@").lower()
        for row in items:
            if isinstance(row, dict) and str(row.get("username", "")).lstrip("@").lower() == h:
                row["last_checked_at"] = when.isoformat()
                break
        with self._targets_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(raw, f, sort_keys=False, allow_unicode=True)
