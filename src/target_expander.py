"""
target_expander.py

Suggests new target accounts from follow graph; writes data/suggested_targets.md for human review.
Key dependencies: target_manager, twitter_client, pathlib
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.config_loader import AppConfig
from src.target_manager import TargetManager
from src.twitter_client import TwitterAPIError, TwitterClient


class TargetExpander:
    def __init__(
        self,
        cfg: AppConfig,
        twitter: TwitterClient,
        targets: TargetManager,
        logger: logging.Logger | None = None,
        output_path: str | Path | None = None,
    ):
        self._cfg = cfg
        self._twitter = twitter
        self._targets = targets
        self._log = logger or logging.getLogger("twitter_bot")
        self._out = Path(output_path) if output_path else Path("data/suggested_targets.md")

    def run(self) -> Path:
        existing = {a.username.lower() for a in self._targets.load_targets()}
        suggestions: list[str] = []
        for acc in self._targets.get_accounts_to_check(limit=3):
            try:
                uid = self._twitter.get_user_id(acc.username)
                following = self._twitter.get_following_usernames(uid, max_results=20)
                for h in following:
                    hl = h.lower()
                    if hl and hl not in existing:
                        suggestions.append(h)
            except TwitterAPIError as e:
                self._log.warning("expander skip", extra={"metadata": {"account": acc.username, "err": str(e)}})

        uniq: list[str] = []
        seen: set[str] = set()
        for s in suggestions:
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            uniq.append(s)
            if len(uniq) >= 5:
                break

        lines = [
            "# Suggested targets (human review required)",
            "",
            "Do not auto-follow. Add entries to data/targets.yaml manually if appropriate.",
            "",
        ]
        for s in uniq:
            lines.append(f"- @{s}")
        if not uniq:
            lines.append("- (no suggestions — check API access for following list)")
        self._out.parent.mkdir(parents=True, exist_ok=True)
        self._out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self._out
