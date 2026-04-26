"""Tests for target_expander."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import yaml

from src.config_loader import AppConfig
from src.target_expander import TargetExpander
from src.target_manager import TargetManager
from src.twitter_client import TwitterClient
from tests.fixtures import MINIMAL_CONFIG_DICT


def test_target_expander_writes_md(tmp_path: Path) -> None:
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {
        **MINIMAL_CONFIG_DICT["paths"],
        "targets_file": str(tmp_path / "t.yaml"),
    }
    cfg = AppConfig.model_validate(d)
    (tmp_path / "t.yaml").write_text(
        yaml.safe_dump({"targets": [{"username": "seed", "priority": 1, "enabled": True}]}),
        encoding="utf-8",
    )
    tw = MagicMock(spec=TwitterClient)
    tw.get_user_id.return_value = "99"
    tw.get_following_usernames.return_value = ["a", "b", "c"]
    tm = TargetManager(cfg, twitter=tw)
    ex = TargetExpander(cfg, tw, tm, output_path=tmp_path / "suggested.md")
    out = ex.run()
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "a" in text
