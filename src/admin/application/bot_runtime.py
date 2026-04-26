"""
Singleton bot worker: scheduler + MainLoop in a background thread with cooperative stop.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import date
from typing import Any

from src.config_loader import AppConfig
from src.knowledge_store import KnowledgeStore
from src.llm_client import LLMClient
from src.logger import setup_logging
from src.main_loop import MainLoop
from src.scheduler import Scheduler
from src.twitter_client import TwitterClient
from src.admin.domain.runtime_state import RuntimeState
from src.admin.infrastructure.config_repository import ConfigRepository
from src.admin.infrastructure.log_broadcaster import BroadcastLogHandler, LogBroadcaster


class BotRuntimeService:
    """
    Single runtime instance for the admin panel.
    """

    _instance: BotRuntimeService | None = None
    _instance_lock = threading.Lock()

    def __init__(self, config_path: str | None = None) -> None:
        self._repo = ConfigRepository(config_path)
        self._state = RuntimeState.stopped
        self._state_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._last_summary: dict[str, Any] | None = None
        self._last_error: str | None = None
        self._broadcaster = LogBroadcaster()
        self._broadcast_handler: BroadcastLogHandler | None = None
        self._log = logging.getLogger("twitter_bot.admin")

    @classmethod
    def instance(cls, config_path: str | None = None) -> BotRuntimeService:
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls(config_path)
            return cls._instance

    @property
    def broadcaster(self) -> LogBroadcaster:
        return self._broadcaster

    def state(self) -> RuntimeState:
        with self._state_lock:
            return self._state

    def _set_state(self, s: RuntimeState) -> None:
        with self._state_lock:
            self._state = s

    def last_summary(self) -> dict[str, Any] | None:
        return self._last_summary

    def last_error(self) -> str | None:
        return self._last_error

    def attach_log_broadcast(self, log: logging.Logger) -> None:
        if self._broadcast_handler is not None:
            log.removeHandler(self._broadcast_handler)
        self._broadcast_handler = BroadcastLogHandler(self._broadcaster)
        self._broadcast_handler.setLevel(logging.DEBUG)
        log.addHandler(self._broadcast_handler)

    def detach_log_broadcast(self, log: logging.Logger) -> None:
        if self._broadcast_handler is not None:
            log.removeHandler(self._broadcast_handler)
            self._broadcast_handler = None

    def _interruptible_sleep(self, sched: Scheduler, seconds: float) -> None:
        end = time.monotonic() + max(0.0, seconds)
        while time.monotonic() < end:
            if self._stop.is_set():
                return
            time.sleep(min(1.0, end - time.monotonic()))

    def _loop_body(self) -> None:
        cfg = self._repo.load_app_config()
        log = setup_logging(cfg)
        self.attach_log_broadcast(log)
        store = KnowledgeStore(cfg)
        twitter = TwitterClient(cfg, logger=log, replied_checker=store.has_replied_to)
        llm = LLMClient(cfg, logger=log)
        sched = Scheduler(cfg, logger=log)
        loop = MainLoop(cfg, twitter=twitter, store=store, llm=llm, logger=log)

        try:
            while not self._stop.is_set():
                if sched.is_paused():
                    self._interruptible_sleep(sched, 1.0)
                    continue
                sched.record_run_start()
                try:
                    summary = loop.run_cycle()
                    self._last_summary = summary
                    self._last_error = None
                    log.info("cycle done", extra={"metadata": summary})
                    errs = summary.get("errors", 0)
                    sched.record_run_errors(errs)
                    if errs >= 3:
                        log.error("too many errors; pausing scheduler")
                        sched.set_paused(True)
                except Exception as e:
                    self._last_error = str(e)
                    log.exception("cycle error")
                if self._stop.is_set():
                    break
                delay = sched.next_interval_seconds()
                self._interruptible_sleep(sched, delay)
        finally:
            self.detach_log_broadcast(log)
            try:
                llm.close()
            except Exception:
                pass
            try:
                store.close()
            except Exception:
                pass

    def start(self) -> None:
        with self._state_lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._set_state(RuntimeState.starting)
            self._stop.clear()
        self._thread = threading.Thread(target=self._thread_target, name="bot-runtime", daemon=True)
        self._thread.start()

    def _thread_target(self) -> None:
        try:
            self._set_state(RuntimeState.running)
            self._loop_body()
        finally:
            self._set_state(RuntimeState.stopped)

    def stop(self) -> None:
        self._set_state(RuntimeState.stopping)
        self._stop.set()
        t = self._thread
        if t is not None:
            t.join(timeout=120.0)
        self._thread = None
        self._set_state(RuntimeState.stopped)

    def pause(self) -> None:
        cfg = self._repo.load_app_config()
        Scheduler(cfg, logger=self._log).set_paused(True)

    def resume(self) -> None:
        cfg = self._repo.load_app_config()
        Scheduler(cfg, logger=self._log).set_paused(False)

    def status_snapshot(self) -> dict[str, Any]:
        cfg = None
        try:
            cfg = self._repo.load_app_config(skip_secret_validation=True)
        except Exception as e:
            return {
                "runtime": self.state().value,
                "config_error": str(e),
                "last_summary": self._last_summary,
                "last_error": self._last_error,
            }
        sched = Scheduler(cfg, logger=self._log)
        st = sched.load_state()
        store = KnowledgeStore(cfg)
        try:
            replies_today = store.get_daily_reply_count(date.today())
        finally:
            store.close()
        return {
            "runtime": self.state().value,
            "paused": st.paused,
            "last_run_at": st.last_run_at,
            "last_run_errors": st.last_run_errors,
            "replies_today": replies_today,
            "last_summary": self._last_summary,
            "last_error": self._last_error,
            "dry_run": cfg.bot.dry_run,
        }

    def run_dry_run_once(self) -> dict[str, Any]:
        cfg = self._repo.load_app_config()
        log = setup_logging(cfg)
        self.attach_log_broadcast(log)
        data = cfg.model_dump()
        data["bot"] = {**data["bot"], "dry_run": True}
        cfg_run = AppConfig.model_validate(data)
        store = KnowledgeStore(cfg_run)
        twitter = TwitterClient(cfg_run, logger=log, replied_checker=store.has_replied_to)
        llm = LLMClient(cfg_run, logger=log)
        loop = MainLoop(cfg_run, twitter=twitter, store=store, llm=llm, logger=log)
        try:
            return loop.run_cycle()
        finally:
            self.detach_log_broadcast(log)
            llm.close()
            store.close()
