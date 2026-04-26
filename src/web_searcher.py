"""
web_searcher.py

Web search via DuckDuckGo / Serper / Brave; cache; LLM summary.
Key dependencies: httpx, duckduckgo_search, llm_client, config_loader, models
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from src.config_loader import AppConfig
from src.llm_client import LLMClient, LLMError
from src.models import SearchContext, SearchResultItem
from src.prompt_util import load_prompt_body


class WebSearcher:
    def __init__(self, cfg: AppConfig, llm: LLMClient, logger: logging.Logger | None = None):
        self._cfg = cfg
        self._llm = llm
        self._log = logger or logging.getLogger("twitter_bot")
        self._cache: dict[str, tuple[float, list[SearchResultItem]]] = {}
        self._summariser = load_prompt_body("web_search_summariser")
        self._http = httpx.Client(timeout=30.0)

    def _ttl_seconds(self) -> float:
        return max(60.0, self._cfg.search.cache_ttl_minutes * 60)

    def _duck(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        from duckduckgo_search import DDGS

        out: list[SearchResultItem] = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                out.append(
                    SearchResultItem(
                        title=str(r.get("title", "")),
                        url=str(r.get("href", r.get("url", ""))),
                        snippet=str(r.get("body", "")),
                    )
                )
        return out

    def _serper(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        key = self._cfg.search.serper_api_key
        r = self._http.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": max_results},
        )
        r.raise_for_status()
        data = r.json()
        organic = data.get("organic") or []
        return [
            SearchResultItem(
                title=str(item.get("title", "")),
                url=str(item.get("link", "")),
                snippet=str(item.get("snippet", "")),
            )
            for item in organic[:max_results]
        ]

    def _brave(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        key = self._cfg.search.brave_api_key
        r = self._http.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": key, "Accept": "application/json"},
            params={"q": query, "count": max_results},
        )
        r.raise_for_status()
        data = r.json()
        web = data.get("web", {}).get("results") or []
        return [
            SearchResultItem(
                title=str(item.get("title", "")),
                url=str(item.get("url", "")),
                snippet=str(item.get("description", "")),
            )
            for item in web[:max_results]
        ]

    def _fetch_results(self, query: str) -> list[SearchResultItem]:
        prov = self._cfg.search.provider
        if prov == "duckduckgo":
            return self._duck(query)
        if prov == "serper":
            return self._serper(query)
        if prov == "brave":
            return self._brave(query)
        raise ValueError(f"unknown search provider: {prov}")

    def search(self, query: str) -> SearchContext:
        now = time.time()
        q = query.strip()
        if not q:
            return SearchContext(query=q, results=[], summary="", searched_at=datetime.now(timezone.utc))

        hit = self._cache.get(q)
        if hit and now - hit[0] < self._ttl_seconds():
            results = hit[1]
        else:
            try:
                results = self._fetch_results(q)
            except Exception as e:
                self._log.warning("search failed", extra={"metadata": {"error": str(e), "query": q}})
                return SearchContext(
                    query=q,
                    results=[],
                    summary="",
                    searched_at=datetime.now(timezone.utc),
                )
            self._cache[q] = (now, results)

        lines = "\n".join(f"- {r.title}: {r.snippet} ({r.url})" for r in results[:5])
        user = f"tweet context query: {q}\n\nresults:\n{lines or '(none)'}"
        try:
            summary = self._llm.chat(self._summariser, user, max_tokens=400, temperature=0.3)
        except LLMError:
            summary = ""
        return SearchContext(
            query=q,
            results=results,
            summary=summary.strip(),
            searched_at=datetime.now(timezone.utc),
        )

    def close(self) -> None:
        self._http.close()
