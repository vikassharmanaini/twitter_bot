"""Tests for prompt_util."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.prompt_util import load_prompt_body, load_prompt


def test_load_prompt_body_strips_headers() -> None:
    body = load_prompt_body("tweet_analyser")
    assert "JSON" in body
    assert not body.lstrip().startswith("#")


def test_load_prompt_missing_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent_prompt_xyz")
