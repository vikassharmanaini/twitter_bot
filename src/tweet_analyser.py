"""
tweet_analyser.py

Uses LLM to produce structured TweetAnalysis from raw tweet text.
Key dependencies: llm_client, models, prompt_util
"""

from __future__ import annotations

import json
import re
from typing import Any

from src.llm_client import LLMClient, LLMError
from src.models import Sentiment, TechnicalLevel, TweetAnalysis, TweetType
from src.prompt_util import load_prompt_body


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"no JSON object in LLM output: {text[:200]}")
    return json.loads(m.group())


class TweetAnalyser:
    def __init__(self, llm: LLMClient, logger: logging.Logger | None = None):
        self._llm = llm
        self._system = load_prompt_body("tweet_analyser")

    def analyse(self, tweet_id: str, tweet_text: str) -> TweetAnalysis:
        user = f"tweet_id: {tweet_id}\n\ntweet text:\n{tweet_text}"
        try:
            raw = self._llm.chat(
                self._system,
                user,
                max_tokens=300,
                temperature=0.2,
            )
        except LLMError:
            raise
        data = _extract_json_object(raw)
        return TweetAnalysis(
            tweet_id=tweet_id,
            topic=str(data.get("topic", "")),
            sentiment=Sentiment(str(data.get("sentiment", "neutral"))),
            tweet_type=TweetType(str(data.get("tweet_type", "opinion"))),
            technical_level=TechnicalLevel(str(data.get("technical_level", "intermediate"))),
            key_entities=[str(x) for x in (data.get("key_entities") or [])],
            requires_web_search=bool(data.get("requires_web_search", False)),
            search_query=data.get("search_query"),
        )
