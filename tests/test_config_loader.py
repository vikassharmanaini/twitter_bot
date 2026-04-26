"""Tests for config_loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config_loader import AppConfig, load_config, load_raw_yaml, merge_defaults
from tests.fixtures import MINIMAL_CONFIG_DICT, write_config_yaml


def test_config_loader_happy_path_writes_and_loads(tmp_path: Path) -> None:
    p = write_config_yaml(tmp_path / "config.yaml")
    cfg = load_config(p, skip_secret_validation=False)
    assert isinstance(cfg, AppConfig)
    assert cfg.openrouter.primary_model == "test/model-a"
    assert cfg.bot.dry_run is True


def test_config_loader_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.yaml")


def test_config_loader_placeholder_api_key_raises(tmp_path: Path) -> None:
    write_config_yaml(tmp_path / "c.yaml", {"openrouter": {"api_key": "REPLACE_ME"}})
    with pytest.raises(ValueError, match="openrouter.api_key"):
        load_config(tmp_path / "c.yaml")


def test_config_loader_serper_requires_key(tmp_path: Path) -> None:
    write_config_yaml(
        tmp_path / "c.yaml",
        {"search": {"provider": "serper", "serper_api_key": ""}},
    )
    with pytest.raises(ValueError, match="serper_api_key"):
        load_config(tmp_path / "c.yaml")


def test_merge_defaults_adds_nested() -> None:
    raw = {"openrouter": MINIMAL_CONFIG_DICT["openrouter"], "twitter": MINIMAL_CONFIG_DICT["twitter"]}
    m = merge_defaults(raw)
    assert "bot" in m and "logging" in m


def test_load_raw_yaml_invalid_top_level(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_raw_yaml(p)
