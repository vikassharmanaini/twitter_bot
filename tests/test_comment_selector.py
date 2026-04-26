"""Tests for comment_selector."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.comment_selector import CommentSelector, _parse_scores
from src.llm_client import LLMClient


def test_parse_scores() -> None:
    raw = 'data [{"human_likeness":9,"relevance":8,"engagement_potential":7,"risk_score":2}]'
    s = _parse_scores(raw)
    assert s[0]["risk_score"] == 2


def test_select_best_picks_highest() -> None:
    llm = MagicMock(spec=LLMClient)
    llm.chat.return_value = (
        '[{"human_likeness":5,"relevance":5,"engagement_potential":5,"risk_score":5},'
        '{"human_likeness":9,"relevance":9,"engagement_potential":9,"risk_score":2},'
        '{"human_likeness":1,"relevance":1,"engagement_potential":1,"risk_score":9}]'
    )
    sel = CommentSelector(llm)
    best, allc = sel.select_best("tweet", ["a", "b", "c"])
    assert best.text == "b"
    assert best.risk_score == 2
