"""Tests for tweet_analyser."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.llm_client import LLMClient
from src.models import Sentiment, TweetType
from src.tweet_analyser import TweetAnalyser, _extract_json_object


def test_extract_json_object() -> None:
    d = _extract_json_object('prefix {"topic": "x", "sentiment": "neutral"} suffix')
    assert d["topic"] == "x"


def test_analyse_happy_path() -> None:
    llm = MagicMock(spec=LLMClient)
    llm.chat.return_value = (
        '{"topic":"Rust","sentiment":"excited","tweet_type":"announcement",'
        '"technical_level":"expert","key_entities":["Rust"],'
        '"requires_web_search":false,"search_query":null}'
    )
    ta = TweetAnalyser(llm)
    a = ta.analyse("1", "Rust 1.75 shipped!")
    assert a.tweet_id == "1"
    assert a.sentiment == Sentiment.excited
    assert a.tweet_type == TweetType.announcement
