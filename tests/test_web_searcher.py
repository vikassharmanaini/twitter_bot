"""Tests for web_searcher."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.config_loader import AppConfig
from src.llm_client import LLMClient
from src.web_searcher import WebSearcher
from tests.fixtures import MINIMAL_CONFIG_DICT


def _cfg() -> AppConfig:
    return AppConfig.model_validate(MINIMAL_CONFIG_DICT)


def test_search_empty_query() -> None:
    ws = WebSearcher(_cfg(), MagicMock(spec=LLMClient))
    ctx = ws.search("   ")
    assert ctx.results == []
    ws.close()


@patch("src.web_searcher.WebSearcher._duck")
def test_search_uses_cache(mock_duck: MagicMock) -> None:
    cfg = _cfg()
    llm = MagicMock(spec=LLMClient)
    llm.chat.return_value = "summary text"
    mock_duck.return_value = []
    ws = WebSearcher(cfg, llm)
    ws.search("q1")
    ws.search("q1")
    assert mock_duck.call_count == 1
    ws.close()


@patch("src.web_searcher.WebSearcher._fetch_results")
def test_search_degrades_on_failure(mock_fetch: MagicMock) -> None:
    mock_fetch.side_effect = RuntimeError("network")
    ws = WebSearcher(_cfg(), MagicMock(spec=LLMClient))
    ctx = ws.search("x")
    assert ctx.summary == ""
    ws.close()
