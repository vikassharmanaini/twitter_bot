"""Tests for scheduler."""

from __future__ import annotations

from pathlib import Path

from freezegun import freeze_time

from src.config_loader import AppConfig
from src.scheduler import BotState, Scheduler
from tests.fixtures import MINIMAL_CONFIG_DICT


def _sched(tmp_path: Path) -> Scheduler:
    d = {**MINIMAL_CONFIG_DICT}
    d["paths"] = {**MINIMAL_CONFIG_DICT["paths"], "bot_state_file": str(tmp_path / "state.json")}
    cfg = AppConfig.model_validate(d)
    return Scheduler(cfg)


def test_pause_roundtrip(tmp_path: Path) -> None:
    s = _sched(tmp_path)
    s.set_paused(True)
    assert s.is_paused()
    s.set_paused(False)
    assert not s.is_paused()


def test_next_interval_in_range(tmp_path: Path) -> None:
    s = _sched(tmp_path)
    for _ in range(20):
        sec = s.next_interval_seconds()
        base = MINIMAL_CONFIG_DICT["bot"]["schedule_interval_minutes"] * 60
        assert 0.7 * base <= sec <= 1.3 * base


def test_record_run(tmp_path: Path) -> None:
    s = _sched(tmp_path)
    with freeze_time("2024-01-01T12:00:00+00:00"):
        s.record_run_start()
    st = s.load_state()
    assert st.last_run_at is not None
