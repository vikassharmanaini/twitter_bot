"""
Replies, stats, DB summary, clear history.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query

from src.admin.api.deps import require_admin_token
from src.admin.infrastructure.config_repository import ConfigRepository
from src.config_loader import load_config
from src.knowledge_store import KnowledgeStore

router = APIRouter(tags=["data"])


def _store(repo: ConfigRepository) -> KnowledgeStore:
    cfg = load_config(repo.path, skip_secret_validation=True)
    return KnowledgeStore(cfg)


@router.get("/api/replies/recent", dependencies=[Depends(require_admin_token)])
def recent_replies(
    limit: int = Query(50, ge=1, le=200),
    repo: ConfigRepository = Depends(ConfigRepository),
) -> dict[str, Any]:
    store = _store(repo)
    try:
        return {"items": store.list_recent_replies(limit)}
    finally:
        store.close()


@router.get("/api/stats/weekly", dependencies=[Depends(require_admin_token)])
def weekly_stats(repo: ConfigRepository = Depends(ConfigRepository)) -> dict[str, Any]:
    store = _store(repo)
    try:
        return store.export_weekly_summary_json()
    finally:
        store.close()


@router.get("/api/stats/performance", dependencies=[Depends(require_admin_token)])
def performance_stats(repo: ConfigRepository = Depends(ConfigRepository)) -> dict[str, Any]:
    """Daily aggregates, weekly reply counts by account, recent replies + engagement payload."""
    store = _store(repo)
    try:
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        daily = store.daily_stats_series(21)
        by_account = store.replies_by_account_since(week_ago)
        weekly = store.export_weekly_summary_json()
        recent = store.list_replies_with_engagement(80)
        return {
            "daily": daily,
            "replies_by_account_week": by_account,
            "weekly_reply_count": weekly["count"],
            "recent_replies": recent,
        }
    finally:
        store.close()


@router.get("/api/db/summary", dependencies=[Depends(require_admin_token)])
def db_summary(repo: ConfigRepository = Depends(ConfigRepository)) -> dict[str, Any]:
    store = _store(repo)
    try:
        return {"counts": store.table_row_counts()}
    finally:
        store.close()


@router.post("/api/replies/clear-history", dependencies=[Depends(require_admin_token)])
def clear_history(repo: ConfigRepository = Depends(ConfigRepository)) -> dict[str, str]:
    store = _store(repo)
    try:
        store.clear_replied_history()
        return {"status": "ok"}
    finally:
        store.close()
