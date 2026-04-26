"""
knowledge_updater.py

Daily job: hot topics → web search → knowledge_snippets.
Key dependencies: knowledge_store, web_searcher, llm_client, prompt_util
"""

from __future__ import annotations

import logging

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.llm_client import LLMClient
from src.prompt_util import load_prompt_body
from src.web_searcher import WebSearcher


class KnowledgeUpdater:
    def __init__(
        self,
        cfg: AppConfig,
        store: KnowledgeStore,
        llm: LLMClient,
        searcher: WebSearcher,
        logger: logging.Logger | None = None,
    ):
        self._cfg = cfg
        self._store = store
        self._llm = llm
        self._searcher = searcher
        self._log = logger or logging.getLogger("twitter_bot")
        self._system = load_prompt_body("knowledge_updater")

    def run_daily(self) -> int:
        topics = self._store.hot_topics(min_count=3)
        added = 0
        for topic in topics:
            q = f"latest news on {topic}"
            ctx = self._searcher.search(q)
            if not ctx.results:
                continue
            user = f"Topic: {topic}\n\nSnippets:\n{ctx.summary}\n"
            summary = self._llm.chat(self._system, user, max_tokens=500, temperature=0.3)
            url = ctx.results[0].url if ctx.results else ""
            self._store.add_knowledge_snippet(topic, summary.strip(), url)
            added += 1
        self._log.info("knowledge updater done", extra={"metadata": {"snippets_added": added}})
        return added
