"""
safety_filter.py

Pre-post checks: length, duplicates, cooldown, daily cap, blacklist, similarity, bot-reveal LLM.
Key dependencies: knowledge_store, llm_client, config_loader, models
"""

from __future__ import annotations

import logging
import random
from difflib import SequenceMatcher
from datetime import datetime, timedelta, timezone

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.llm_client import LLMClient
from src.models import SafetyDecision, SafetyResult
from src.prompt_util import load_prompt_body


def _similarity(a: str, b: str) -> float:
    a, b = a.lower().strip(), b.lower().strip()
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


class SafetyFilter:
    def __init__(
        self,
        cfg: AppConfig,
        store: KnowledgeStore,
        llm: LLMClient | None = None,
        logger: logging.Logger | None = None,
    ):
        self._cfg = cfg
        self._store = store
        self._llm = llm
        self._log = logger or logging.getLogger("twitter_bot")
        self._bot_check_system = load_prompt_body("bot_reveal_check")

    def evaluate(
        self,
        tweet_id: str,
        target_account: str,
        comment: str,
        *,
        author_followers: int | None = None,
        tweet_text: str | None = None,
        skip_bot_llm: bool = False,
    ) -> SafetyResult:
        if len(comment) > 280:
            return SafetyResult(decision=SafetyDecision.REJECTED_WITH_REASON, reason="comment too long")

        if self._store.has_replied_to(tweet_id):
            return SafetyResult(decision=SafetyDecision.REJECTED_WITH_REASON, reason="already replied to tweet")

        cap = min(self._cfg.safety.daily_reply_cap, self._cfg.bot.max_replies_per_day)
        if self._store.get_daily_reply_count() >= cap:
            return SafetyResult(decision=SafetyDecision.REJECTED_WITH_REASON, reason="daily reply cap reached")

        last = self._store.last_post_time()
        if last:
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - last
            if delta < timedelta(minutes=self._cfg.safety.min_minutes_between_posts):
                return SafetyResult(decision=SafetyDecision.REJECTED_WITH_REASON, reason="cooldown between posts")

        if self._store.replies_today_for_account(target_account) >= 1:
            return SafetyResult(decision=SafetyDecision.REJECTED_WITH_REASON, reason="max one reply per target per day")

        low = (comment or "").lower()
        for w in self._cfg.safety.blacklisted_words:
            if w and w.lower() in low:
                return SafetyResult(decision=SafetyDecision.REJECTED_WITH_REASON, reason=f"blacklisted word: {w}")

        if author_followers is not None and author_followers < self._cfg.bot.min_target_followers:
            return SafetyResult(
                decision=SafetyDecision.REJECTED_WITH_REASON,
                reason=f"author below min followers ({author_followers})",
            )

        if tweet_text:
            tl = tweet_text.lower()
            for kw in self._cfg.safety.tragedy_keywords:
                if kw and kw.lower() in tl:
                    return SafetyResult(decision=SafetyDecision.REJECTED_WITH_REASON, reason="tragedy/sensitive content")

        recent = self._store.recent_reply_texts(limit=30)
        max_sim = self._cfg.safety.max_similarity_to_recent
        for prev in recent:
            if _similarity(comment, prev) > max_sim:
                return SafetyResult(decision=SafetyDecision.REJECTED_WITH_REASON, reason="too similar to recent reply")

        if not skip_bot_llm and self._llm:
            ans = self._llm.chat(
                self._bot_check_system,
                f"Reply text:\n{comment}",
                max_tokens=150,
                temperature=0.0,
            ).strip().upper()
            if ans.startswith("YES"):
                return SafetyResult(decision=SafetyDecision.REGENERATE, reason="possible bot reveal")

        return SafetyResult(decision=SafetyDecision.APPROVED, reason="ok")

    def pre_post_delay_seconds(self) -> int:
        return random.randint(5, 30)
