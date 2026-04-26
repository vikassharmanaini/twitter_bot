"""Tests for target_manager."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from src.config_loader import AppConfig
from src.target_manager import TargetManager, _parse_targets_doc
from src.twitter_client import TwitterClient
from tests.fixtures import MINIMAL_CONFIG_DICT


def _cfg(tmp_path: Path) -> AppConfig:
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {
        **MINIMAL_CONFIG_DICT["paths"],
        "targets_file": str(tmp_path / "targets.yaml"),
        "target_cache_file": str(tmp_path / "cache.json"),
    }
    return AppConfig.model_validate(d)


def test_parse_targets_doc() -> None:
    raw = {
        "targets": [
            {"username": "@a", "category": "x", "priority": 1, "enabled": True},
            {"username": "b", "enabled": False},
        ]
    }
    acc = _parse_targets_doc(raw)
    assert acc[0].username == "a"
    assert acc[1].enabled is False


def test_get_accounts_to_check_sorts_by_priority(tmp_path: Path) -> None:
    tfile = tmp_path / "targets.yaml"
    tfile.write_text(
        yaml.safe_dump(
            {
                "targets": [
                    {"username": "low", "priority": 3},
                    {"username": "high", "priority": 1},
                ]
            }
        ),
        encoding="utf-8",
    )
    cfg = _cfg(tmp_path)
    tm = TargetManager(cfg)
    ac = tm.get_accounts_to_check()
    assert [a.username for a in ac] == ["high", "low"]


def test_resolve_user_id_uses_cache(tmp_path: Path) -> None:
    tfile = tmp_path / "targets.yaml"
    tfile.write_text(
        yaml.safe_dump({"targets": [{"username": "cached", "priority": 1}]}),
        encoding="utf-8",
    )
    cache = tmp_path / "cache.json"
    cache.write_text('{"cached": "uid99"}', encoding="utf-8")
    cfg = _cfg(tmp_path)
    tm = TargetManager(cfg, twitter=None)
    ac = tm.load_targets()
    assert ac[0].user_id == "uid99"


def test_targets_file_missing_raises(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    tm = TargetManager(cfg)
    with pytest.raises(FileNotFoundError):
        tm.load_targets()


def test_parse_targets_invalid_list_raises() -> None:
    with pytest.raises(ValueError, match="list"):
        _parse_targets_doc({"targets": "bad"})


def test_mark_checked_updates_yaml(tmp_path: Path) -> None:
    tfile = tmp_path / "targets.yaml"
    tfile.write_text(
        yaml.safe_dump({"targets": [{"username": "u1", "priority": 1}]}),
        encoding="utf-8",
    )
    cfg = _cfg(tmp_path)
    tm = TargetManager(cfg)
    tm.mark_checked("u1")
    data = yaml.safe_load(tfile.read_text(encoding="utf-8"))
    assert "last_checked_at" in data["targets"][0]


def test_resolve_user_id_calls_twitter(tmp_path: Path) -> None:
    tfile = tmp_path / "targets.yaml"
    tfile.write_text(
        yaml.safe_dump({"targets": [{"username": "newuser", "priority": 1}]}),
        encoding="utf-8",
    )
    cfg = _cfg(tmp_path)
    tw = Mock(spec=TwitterClient)
    tw.get_user_id.return_value = "55"
    tm = TargetManager(cfg, twitter=tw)
    ac = tm.load_targets()
    uid = tm.resolve_user_id(ac[0])
    assert uid == "55"
    tw.get_user_id.assert_called_once_with("newuser")
