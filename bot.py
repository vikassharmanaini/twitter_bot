#!/usr/bin/env python3
"""
bot.py — CLI entry for Twitter Dev-Bot.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

from src.config_loader import load_config
from src.knowledge_store import KnowledgeStore
from src.knowledge_updater import KnowledgeUpdater
from src.llm_client import LLMClient
from src.logger import setup_logging
from src.main_loop import MainLoop
from src.performance_analyser import PerformanceAnalyser
from src.report_generator import write_report
from src.scheduler import Scheduler
from src.target_expander import TargetExpander
from src.target_manager import TargetManager
from src.twitter_client import TwitterClient


def _bootstrap(config_path: str | None):
    cfg = load_config(config_path)
    log = setup_logging(cfg)
    store = KnowledgeStore(cfg)
    twitter = TwitterClient(cfg, logger=log, replied_checker=store.has_replied_to)
    llm = LLMClient(cfg, logger=log)
    return cfg, log, store, twitter, llm


def cmd_start(args: argparse.Namespace) -> int:
    cfg, log, store, twitter, llm = _bootstrap(args.config)
    sched = Scheduler(cfg, logger=log)
    if sched.is_paused():
        log.warning("bot is paused; use 'resume' or clear bot_state.json")
        return 1
    log.info("scheduler start", extra={"metadata": {"interval_min": cfg.bot.schedule_interval_minutes}})
    loop = MainLoop(cfg, twitter=twitter, store=store, llm=llm, logger=log)
    while not sched.is_paused():
        sched.record_run_start()
        try:
            summary = loop.run_cycle()
            sched.record_run_errors(summary.get("errors", 0))
            log.info("cycle done", extra={"metadata": summary})
            if summary.get("errors", 0) >= 3:
                log.error("too many errors; pausing")
                sched.set_paused(True)
                return 1
        except KeyboardInterrupt:
            log.info("interrupt")
            return 0
        sched.sleep_until_next()
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    cfg, log, _, _, _ = _bootstrap(args.config)
    Scheduler(cfg, logger=log).set_paused(True)
    log.info("paused bot via state file")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    cfg, log, _, _, _ = _bootstrap(args.config)
    Scheduler(cfg, logger=log).set_paused(False)
    log.info("resumed bot")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    cfg, _, store, _, _ = _bootstrap(args.config)
    sched = Scheduler(cfg)
    st = sched.load_state()
    print(
        json.dumps(
            {
                "paused": st.paused,
                "last_run_at": st.last_run_at,
                "last_errors": st.last_run_errors,
                "replies_today": store.get_daily_reply_count(date.today()),
            },
            indent=2,
        )
    )
    return 0


def cmd_dry_run(args: argparse.Namespace) -> int:
    cfg, log, store, twitter, llm = _bootstrap(args.config)
    if not cfg.bot.dry_run:
        log.warning("config bot.dry_run is false; forcing dry-run for this command only")
    cfg.bot.dry_run = True
    loop = MainLoop(cfg, twitter=twitter, store=store, llm=llm, logger=log)
    summary = loop.run_cycle()
    print(json.dumps(summary, indent=2))
    return 0


def cmd_add_target(args: argparse.Namespace) -> int:
    cfg, _, _, _, _ = _bootstrap(args.config)
    path = Path(cfg.paths.targets_file)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {"targets": []}
    if not isinstance(raw, dict):
        raw = {"targets": []}
    targets = list(raw.get("targets") or [])
    h = args.handle.lstrip("@")
    targets.append({"username": h, "category": args.category or "General", "priority": 3, "enabled": True})
    raw["targets"] = targets
    path.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"added @{h}")
    return 0


def cmd_remove_target(args: argparse.Namespace) -> int:
    cfg, _, _, _, _ = _bootstrap(args.config)
    path = Path(cfg.paths.targets_file)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    targets = raw.get("targets") or []
    h = args.handle.lstrip("@").lower()
    for row in targets:
        if isinstance(row, dict) and str(row.get("username", "")).lstrip("@").lower() == h:
            row["enabled"] = False
    raw["targets"] = targets
    path.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"disabled @{h}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    cfg, _, store, _, _ = _bootstrap(args.config)
    print(json.dumps(store.export_weekly_summary_json(), indent=2)[:8000])
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    cfg, _, store, _, _ = _bootstrap(args.config)
    for r in store.list_recent_replies(10):
        print(
            f"{r['posted_at']} | @{r['account']} | {r['reply_text'][:120]} | id={r['tweet_id']}"
        )
    return 0


def cmd_clear_history(args: argparse.Namespace) -> int:
    cfg, _, store, _, _ = _bootstrap(args.config)
    store.clear_replied_history()
    print("cleared replied_tweets")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    cfg, _, store, _, _ = _bootstrap(args.config)
    p = write_report(store, args.out)
    print(str(p.resolve()))
    return 0


def cmd_knowledge_update(args: argparse.Namespace) -> int:
    cfg, log, store, _, llm = _bootstrap(args.config)
    from src.web_searcher import WebSearcher

    ws = WebSearcher(cfg, llm, logger=log)
    ku = KnowledgeUpdater(cfg, store, llm, ws, logger=log)
    n = ku.run_daily()
    ws.close()
    print(f"snippets added: {n}")
    return 0


def cmd_performance(args: argparse.Namespace) -> int:
    cfg, log, store, twitter, llm = _bootstrap(args.config)
    pa = PerformanceAnalyser(cfg, store, twitter, llm, logger=log)
    p = pa.run_weekly()
    print(str(p))
    return 0


def cmd_suggest_targets(args: argparse.Namespace) -> int:
    cfg, log, _, twitter, _ = _bootstrap(args.config)
    tm = TargetManager(cfg, twitter=twitter, logger=log)
    ex = TargetExpander(cfg, twitter, tm, logger=log)
    p = ex.run()
    print(str(p))
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    """Load config and log OK (smoke test)."""
    _, log, _, _, _ = _bootstrap(args.config)
    log.info("bootstrap OK")
    print("bootstrap OK")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="bot.py")
    p.add_argument("--config", default=None, help="Path to config.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("start", help="Run scheduler loop").set_defaults(func=cmd_start)
    sub.add_parser("stop", help="Pause via bot_state.json").set_defaults(func=cmd_stop)
    sub.add_parser("resume", help="Unpause").set_defaults(func=cmd_resume)
    sub.add_parser("status", help="Show state").set_defaults(func=cmd_status)
    sub.add_parser("dry-run", help="One cycle without posting").set_defaults(func=cmd_dry_run)
    sub.add_parser("bootstrap", help="Verify config loads").set_defaults(func=cmd_bootstrap)

    ap = sub.add_parser("add-target", help="Add target handle")
    ap.add_argument("handle")
    ap.add_argument("--category", default="")
    ap.set_defaults(func=cmd_add_target)

    rp = sub.add_parser("remove-target", help="Disable target handle")
    rp.add_argument("handle")
    rp.set_defaults(func=cmd_remove_target)

    sub.add_parser("stats", help="Weekly JSON stats").set_defaults(func=cmd_stats)
    sub.add_parser("review", help="Last 10 replies").set_defaults(func=cmd_review)
    sub.add_parser("clear-history", help="Wipe replied_tweets").set_defaults(func=cmd_clear_history)

    rpt = sub.add_parser("report", help="Write report.html")
    rpt.add_argument("--out", default="report.html")
    rpt.set_defaults(func=cmd_report)

    sub.add_parser("knowledge-update", help="Run knowledge updater").set_defaults(func=cmd_knowledge_update)
    sub.add_parser("performance", help="Run performance analyser").set_defaults(func=cmd_performance)
    sub.add_parser("suggest-targets", help="Write suggested_targets.md").set_defaults(func=cmd_suggest_targets)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
