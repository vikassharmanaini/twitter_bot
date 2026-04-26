"""Tests for comment_generator."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.comment_generator import CommentGenerator, _split_candidates
from src.config_loader import AppConfig
from src.llm_client import LLMClient
from src.models import SearchContext, Sentiment, TechnicalLevel, TweetAnalysis, TweetType
from tests.fixtures import MINIMAL_CONFIG_DICT


def test_split_candidates() -> None:
    t = "a\n---\nb\n---\nc"
    assert _split_candidates(t) == ["a", "b", "c"]


def test_generate_trims_length() -> None:
    cfg = AppConfig.model_validate(MINIMAL_CONFIG_DICT)
    llm = MagicMock(spec=LLMClient)
    long_line = "x" * 300
    llm.chat.return_value = f"{long_line}\n---\n{long_line}\n---\n{long_line}"
    cg = CommentGenerator(cfg, llm)
    analysis = TweetAnalysis(
        tweet_id="1",
        topic="t",
        sentiment=Sentiment.neutral,
        tweet_type=TweetType.opinion,
        technical_level=TechnicalLevel.intermediate,
    )
    out = cg.generate(analysis, "hello", None)
    assert all(len(c) <= 260 for c in out)
