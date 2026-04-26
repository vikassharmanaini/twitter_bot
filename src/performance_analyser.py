"""
performance_analyser.py

Weekly: fetch engagement for replies, LLM insights → performance_insights.md.
Key dependencies: knowledge_store, twitter_client, llm_client, pathlib
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.llm_client import LLMClient
from src.prompt_util import load_prompt_body
from src.twitter_client import TwitterClient


class PerformanceAnalyser:
    def __init__(
        self,
        cfg: AppConfig,
        store: KnowledgeStore,
        twitter: TwitterClient,
        llm: LLMClient,
        logger: logging.Logger | None = None,
        output_path: str | Path | None = None,
    ):
        self._cfg = cfg
        self._store = store
        self._twitter = twitter
        self._llm = llm
        self._log = logger or logging.getLogger("twitter_bot")
        self._system = load_prompt_body("performance_analyser")
        self._out = Path(output_path) if output_path else Path("data/performance_insights.md")

    def run_weekly(self) -> Path:
        rows = self._store.weekly_summary_rows()
        metrics: list[dict] = []
        for r in rows[:50]:
            tid = str(r["tweet_id"])
            try:
                pm = self._twitter.get_tweet_public_metrics(tid)
                metrics.append({"tweet_id": tid, "reply_text": r["reply_text"][:200], "metrics": pm})
            except Exception:
                metrics.append({"tweet_id": tid, "reply_text": r["reply_text"][:200], "metrics": {}})

        user = json.dumps(metrics[:20], indent=2)
        insights = self._llm.chat(self._system, user, max_tokens=800, temperature=0.4)
        self._out.parent.mkdir(parents=True, exist_ok=True)
        self._out.write_text(f"# Performance insights\n\n{insights}\n", encoding="utf-8")
        self._log.info("wrote performance insights", extra={"metadata": {"path": str(self._out)}})
        return self._out
