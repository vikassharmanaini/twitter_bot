"""Tests for llm_client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.config_loader import AppConfig
from src.llm_client import LLMClient, LLMError
from tests.fixtures import MINIMAL_CONFIG_DICT


def _cfg() -> AppConfig:
    return AppConfig.model_validate(MINIMAL_CONFIG_DICT)


def test_llm_client_chat_success() -> None:
    cfg = _cfg()
    client = LLMClient(cfg)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "hello"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    client._client = MagicMock()
    client._client.post.return_value = mock_resp
    out = client.chat("sys", "user", max_tokens=100)
    assert out == "hello"
    assert client.usage_summary["prompt_tokens"] == 10


def test_llm_client_budget_exceeded() -> None:
    cfg = _cfg()
    cfg.openrouter.max_tokens_per_run = 5
    client = LLMClient(cfg)
    with pytest.raises(LLMError, match="budget"):
        client.chat("s", "u", max_tokens=100)


def test_llm_client_fallback_on_error() -> None:
    cfg = _cfg()
    client = LLMClient(cfg)
    bad = MagicMock(status_code=500, text="err")
    ok = MagicMock(status_code=200)
    ok.json.return_value = {"choices": [{"message": {"content": "ok"}}], "usage": {}}
    client._client = MagicMock()
    client._client.post.side_effect = [bad, ok]
    out = client.chat("s", "u", max_tokens=200)
    assert out == "ok"
