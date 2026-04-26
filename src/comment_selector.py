"""
comment_selector.py

Scores 3 candidates via LLM and returns best with veto on high risk.
Key dependencies: llm_client, models, prompt_util
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from src.llm_client import LLMClient, LLMError
from src.models import CommentCandidate
from src.prompt_util import load_prompt_body


def _parse_scores(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    m = re.search(r"\[[\s\S]*\]", text)
    if not m:
        raise ValueError(f"no JSON array in scorer output: {text[:200]}")
    data = json.loads(m.group())
    if not isinstance(data, list):
        raise ValueError("scorer JSON must be an array")
    return [d for d in data if isinstance(d, dict)]


class CommentSelector:
    def __init__(self, llm: LLMClient, logger: logging.Logger | None = None):
        self._llm = llm
        self._log = logger or logging.getLogger("twitter_bot")
        self._system = load_prompt_body("comment_scorer")

    def select_best(self, tweet_text: str, candidates: list[str]) -> tuple[CommentCandidate, list[CommentCandidate]]:
        if not candidates:
            raise ValueError("no candidates")
        numbered = "\n\n".join(f"{i+1}. {c}" for i, c in enumerate(candidates[:3]))
        user = f"Original tweet:\n{tweet_text}\n\nCandidates:\n{numbered}"
        raw = self._llm.chat(self._system, user, max_tokens=200, temperature=0.2)
        scores_list = _parse_scores(raw)
        enriched: list[CommentCandidate] = []
        for i, cand in enumerate(candidates[:3]):
            sc = scores_list[i] if i < len(scores_list) else {}
            hl = int(sc.get("human_likeness", sc.get("human_likeness_score", 5)))
            rel = int(sc.get("relevance", sc.get("relevance_score", 5)))
            eng = int(sc.get("engagement_potential", sc.get("engagement_score", 5)))
            risk = int(sc.get("risk_score", 5))
            total = float(hl + rel + eng - risk)
            enriched.append(
                CommentCandidate(
                    text=cand,
                    human_likeness_score=hl,
                    relevance_score=rel,
                    engagement_score=eng,
                    risk_score=risk,
                    total_score=total,
                )
            )
        # veto risk > 7
        viable = [c for c in enriched if c.risk_score <= 7]
        pool = viable if viable else enriched
        best = max(pool, key=lambda c: c.total_score)
        return best, enriched
