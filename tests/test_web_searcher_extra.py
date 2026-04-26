"""Extra web_searcher provider tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx

from src.config_loader import AppConfig
from src.llm_client import LLMClient
from src.web_searcher import WebSearcher
from tests.fixtures import MINIMAL_CONFIG_DICT


def test_serper_provider() -> None:
    d = {**MINIMAL_CONFIG_DICT}
    d["search"] = {**MINIMAL_CONFIG_DICT["search"], "provider": "serper", "serper_api_key": "k"}
    cfg = AppConfig.model_validate(d)
    llm = MagicMock(spec=LLMClient)
    llm.chat.return_value = "sum"
    ws = WebSearcher(cfg, llm)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "organic": [{"title": "T", "link": "http://u", "snippet": "S"}],
    }
    ws._http = MagicMock(spec=httpx.Client)
    ws._http.post.return_value = mock_resp
    ctx = ws.search("q")
    assert len(ctx.results) == 1
    ws.close()


def test_brave_provider() -> None:
    d = {**MINIMAL_CONFIG_DICT}
    d["search"] = {**MINIMAL_CONFIG_DICT["search"], "provider": "brave", "brave_api_key": "bk"}
    cfg = AppConfig.model_validate(d)
    llm = MagicMock(spec=LLMClient)
    llm.chat.return_value = "sum"
    ws = WebSearcher(cfg, llm)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "web": {"results": [{"title": "T", "url": "http://u", "description": "D"}]},
    }
    ws._http = MagicMock(spec=httpx.Client)
    ws._http.get.return_value = mock_resp
    ctx = ws.search("q")
    assert ctx.results[0].title == "T"
    ws.close()

