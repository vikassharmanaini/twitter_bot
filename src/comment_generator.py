"""
comment_generator.py

Generates 3 reply candidates using persona + optional search context.
Key dependencies: llm_client, models, prompt_util, config_loader
"""

from __future__ import annotations

import logging
import re

from src.config_loader import AppConfig
from src.llm_client import LLMClient
from src.models import SearchContext, TweetAnalysis
from src.prompt_util import load_prompt_body


def _split_candidates(text: str) -> list[str]:
    parts = re.split(r"(?m)^---\s*$", text.strip())
    out = [p.strip() for p in parts if p.strip()]
    if len(out) < 3:
        # fallback: take first 3 non-empty lines as single candidates if model forgot separators
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("---")]
        if len(lines) >= 3:
            return lines[:3]
    return out[:3]


class CommentGenerator:
    def __init__(self, cfg: AppConfig, llm: LLMClient, logger: logging.Logger | None = None):
        self._cfg = cfg
        self._llm = llm
        self._log = logger or logging.getLogger("twitter_bot")
        self._system = load_prompt_body("comment_generator")

    def generate(
        self,
        analysis: TweetAnalysis,
        tweet_text: str,
        context: SearchContext | None = None,
        knowledge_extras: str | None = None,
    ) -> list[str]:
        humor = self._cfg.bot.humor_level
        ctx_block = ""
        if context and context.summary:
            ctx_block = f"\nWeb context:\n{context.summary}\n"
        if knowledge_extras:
            ctx_block += f"\nStored knowledge:\n{knowledge_extras}\n"
        user = (
            f"humor_level: {humor}\n"
            f"tweet_type: {analysis.tweet_type.value}\n"
            f"topic: {analysis.topic}\n"
            f"original tweet:\n{tweet_text}\n"
            f"{ctx_block}\n"
            "Produce exactly 3 replies separated by --- as instructed."
        )
        raw = self._llm.chat(self._system, user, max_tokens=600, temperature=0.85)
        cands = _split_candidates(raw)
        trimmed: list[str] = []
        for c in cands:
            t = c.strip()
            if len(t) > 260:
                t = t[:257].rstrip() + "..."
            trimmed.append(t)
        while len(trimmed) < 3:
            trimmed.append(trimmed[-1] if trimmed else "Interesting point.")
        return trimmed[:3]
