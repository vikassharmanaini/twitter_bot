"""
main_loop.py

Orchestrates one cycle: targets → tweets → analyse → search → generate → select → safety → post.
Key dependencies: all service modules
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from src.comment_generator import CommentGenerator
from src.comment_selector import CommentSelector
from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.llm_client import LLMClient
from src.models import SafetyDecision
from src.safety_filter import SafetyFilter
from src.target_manager import TargetManager
from src.tweet_analyser import TweetAnalyser
from src.twitter_client import TwitterClient
from src.web_searcher import WebSearcher


class MainLoop:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        twitter: TwitterClient,
        store: KnowledgeStore,
        llm: LLMClient,
        logger: logging.Logger | None = None,
    ):
        self._cfg = cfg
        self._twitter = twitter
        self._store = store
        self._llm = llm
        self._log = logger or logging.getLogger("twitter_bot")
        self._targets = TargetManager(cfg, twitter=twitter, logger=self._log)
        self._analyser = TweetAnalyser(llm, logger=self._log)
        self._searcher = WebSearcher(cfg, llm, logger=self._log)
        self._gen = CommentGenerator(cfg, llm, logger=self._log)
        self._sel = CommentSelector(llm, logger=self._log)
        self._safety = SafetyFilter(cfg, store, llm=llm, logger=self._log)

    def run_cycle(self) -> dict:
        """Run one processing cycle. Returns summary dict."""
        summary: dict = {"accounts": 0, "posted": 0, "skipped": 0, "errors": 0, "messages": []}
        self._llm.reset_budget()
        limit = self._cfg.bot.accounts_per_cycle
        accounts = self._targets.get_accounts_to_check(limit=limit)
        now = datetime.now(timezone.utc)
        min_age = timedelta(minutes=self._cfg.bot.min_tweet_age_minutes)
        max_age = timedelta(hours=self._cfg.bot.max_tweet_age_hours)

        for acc in accounts:
            summary["accounts"] += 1
            try:
                uid, followers = self._twitter.get_user_profile(acc.username)
                acc.user_id = uid
                if followers < self._cfg.bot.min_target_followers:
                    summary["messages"].append(f"skip {acc.username}: low followers")
                    continue

                tweets = self._twitter.get_recent_tweets(uid, count=10)
                candidates = []
                for tw in tweets:
                    if tw.is_retweet:
                        continue
                    if self._twitter.has_already_replied(tw.tweet_id):
                        continue
                    if tw.created_at.tzinfo is None:
                        tw.created_at = tw.created_at.replace(tzinfo=timezone.utc)
                    age = now - tw.created_at
                    if age < min_age or age > max_age:
                        continue
                    candidates.append(tw)
                if not candidates:
                    summary["skipped"] += 1
                    self._targets.mark_checked(acc.username, now)
                    continue

                best_tw = max(candidates, key=lambda t: t.like_count + t.retweet_count)
                analysis = self._analyser.analyse(best_tw.tweet_id, best_tw.text)
                self._store.bump_topic(analysis.topic, now)

                ctx = None
                if analysis.requires_web_search and analysis.search_query:
                    ctx = self._searcher.search(analysis.search_query)

                snippets = self._store.get_snippets_for_topic(analysis.topic, limit=3)
                know = "\n".join(s["summary"] for s in snippets) if snippets else None
                raw_cands = self._gen.generate(analysis, best_tw.text, ctx, knowledge_extras=know)
                best_comment, _scores = self._sel.select_best(best_tw.text, raw_cands)

                safety = self._safety.evaluate(
                    best_tw.tweet_id,
                    acc.username,
                    best_comment.text,
                    author_followers=followers,
                    tweet_text=best_tw.text,
                    skip_bot_llm=False,
                )

                if safety.decision == SafetyDecision.REGENERATE:
                    raw_cands2 = self._gen.generate(analysis, best_tw.text, ctx, knowledge_extras=know)
                    best_comment, _ = self._sel.select_best(best_tw.text, raw_cands2)
                    safety = self._safety.evaluate(
                        best_tw.tweet_id,
                        acc.username,
                        best_comment.text,
                        author_followers=followers,
                        tweet_text=best_tw.text,
                        skip_bot_llm=True,
                    )

                if safety.decision != SafetyDecision.APPROVED:
                    summary["messages"].append(f"{acc.username}: {safety.decision.value} {safety.reason}")
                    summary["skipped"] += 1
                    self._targets.mark_checked(acc.username, now)
                    continue

                delay = self._safety.pre_post_delay_seconds()
                if self._cfg.bot.dry_run:
                    self._log.info(
                        "dry-run: would post reply",
                        extra={
                            "metadata": {
                                "tweet_id": best_tw.tweet_id,
                                "text": best_comment.text[:100],
                                "delay": delay,
                            }
                        },
                    )
                    summary["messages"].append(f"dry-run would reply to {best_tw.tweet_id}")
                else:
                    time.sleep(delay)
                    self._twitter.post_reply(best_tw.tweet_id, best_comment.text)
                    self._store.record_reply(
                        best_tw.tweet_id,
                        acc.username,
                        best_comment.text,
                        datetime.now(timezone.utc),
                        {
                            "human": best_comment.human_likeness_score,
                            "relevance": best_comment.relevance_score,
                            "engagement": best_comment.engagement_score,
                            "risk": best_comment.risk_score,
                        },
                    )
                    self._store.increment_daily_replies(1)
                    summary["posted"] += 1
                    summary["messages"].append(f"posted to {best_tw.tweet_id}")

                self._targets.mark_checked(acc.username, now)
            except Exception as e:
                summary["errors"] += 1
                self._log.exception("cycle error", extra={"metadata": {"account": acc.username}})
                summary["messages"].append(f"error {acc.username}: {e}")

        usage = self._llm.usage_summary
        self._store.increment_daily_stat(tokens_used=usage["prompt_tokens"] + usage["completion_tokens"], errors=summary["errors"])
        return summary
