"""
Long-running maintenance jobs (same as CLI).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.admin.api.deps import require_admin_token
from src.admin.infrastructure.config_repository import ConfigRepository
from src.config_loader import load_config
from src.knowledge_store import KnowledgeStore
from src.knowledge_updater import KnowledgeUpdater
from src.llm_client import LLMClient
from src.logger import setup_logging
from src.performance_analyser import PerformanceAnalyser
from src.report_generator import write_report
from src.target_expander import TargetExpander
from src.target_manager import TargetManager
from src.twitter_client import TwitterClient
from src.web_searcher import WebSearcher

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/knowledge-update", dependencies=[Depends(require_admin_token)])
def job_knowledge(repo: ConfigRepository = Depends(ConfigRepository)) -> dict[str, int | str]:
    cfg = load_config(repo.path)
    log = setup_logging(cfg)
    store = KnowledgeStore(cfg)
    llm = LLMClient(cfg, logger=log)
    ws = WebSearcher(cfg, llm, logger=log)
    try:
        ku = KnowledgeUpdater(cfg, store, llm, ws, logger=log)
        n = ku.run_daily()
        return {"snippets_added": n, "status": "ok"}
    finally:
        ws.close()
        llm.close()
        store.close()


@router.post("/performance", dependencies=[Depends(require_admin_token)])
def job_performance(repo: ConfigRepository = Depends(ConfigRepository)) -> dict[str, str]:
    cfg = load_config(repo.path)
    log = setup_logging(cfg)
    store = KnowledgeStore(cfg)
    twitter = TwitterClient(cfg, logger=log, replied_checker=store.has_replied_to)
    llm = LLMClient(cfg, logger=log)
    try:
        pa = PerformanceAnalyser(cfg, store, twitter, llm, logger=log)
        p = pa.run_weekly()
        return {"path": str(p), "status": "ok"}
    finally:
        llm.close()
        store.close()


@router.post("/suggest-targets", dependencies=[Depends(require_admin_token)])
def job_suggest(repo: ConfigRepository = Depends(ConfigRepository)) -> dict[str, str]:
    cfg = load_config(repo.path)
    log = setup_logging(cfg)
    twitter = TwitterClient(cfg, logger=log)
    tm = TargetManager(cfg, twitter=twitter, logger=log)
    try:
        ex = TargetExpander(cfg, twitter, tm, logger=log)
        p = ex.run()
        return {"path": str(p), "status": "ok"}
    finally:
        pass


class ReportBody(BaseModel):
    out: str = "report.html"


@router.post("/report", dependencies=[Depends(require_admin_token)])
def job_report(
    body: ReportBody | None = None,
    repo: ConfigRepository = Depends(ConfigRepository),
) -> dict[str, str]:
    cfg = load_config(repo.path)
    store = KnowledgeStore(cfg)
    try:
        out = (body.out if body is not None else "report.html")
        p = write_report(store, out)
        return {"path": str(p.resolve()), "status": "ok"}
    finally:
        store.close()
