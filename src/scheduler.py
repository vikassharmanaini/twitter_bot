"""
scheduler.py

Run interval with jitter; pause/resume via bot_state.json.
Key dependencies: json, random, pathlib, config_loader
"""

from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.config_loader import AppConfig


@dataclass
class BotState:
    paused: bool = False
    last_run_at: str | None = None
    last_run_errors: int = 0


class Scheduler:
    def __init__(self, cfg: AppConfig, logger: logging.Logger | None = None):
        self._cfg = cfg
        self._log = logger or logging.getLogger("twitter_bot")
        self._state_path = Path(cfg.paths.bot_state_file)

    def load_state(self) -> BotState:
        if not self._state_path.is_file():
            return BotState()
        try:
            raw = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return BotState()
        return BotState(
            paused=bool(raw.get("paused", False)),
            last_run_at=raw.get("last_run_at"),
            last_run_errors=int(raw.get("last_run_errors", 0)),
        )

    def save_state(self, state: BotState) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(
            json.dumps(
                {
                    "paused": state.paused,
                    "last_run_at": state.last_run_at,
                    "last_run_errors": state.last_run_errors,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def set_paused(self, paused: bool) -> None:
        st = self.load_state()
        st.paused = paused
        self.save_state(st)

    def is_paused(self) -> bool:
        return self.load_state().paused

    def next_interval_seconds(self) -> float:
        base = self._cfg.bot.schedule_interval_minutes * 60
        jitter_pct = self._cfg.bot.schedule_jitter_percent / 100.0
        lo, hi = base * (1 - jitter_pct), base * (1 + jitter_pct)
        return float(random.uniform(lo, hi))

    def sleep_until_next(self) -> None:
        time.sleep(self.next_interval_seconds())

    def record_run_start(self) -> None:
        st = self.load_state()
        st.last_run_at = datetime.now(timezone.utc).isoformat()
        self.save_state(st)

    def record_run_errors(self, n: int) -> None:
        st = self.load_state()
        st.last_run_errors = n
        self.save_state(st)
