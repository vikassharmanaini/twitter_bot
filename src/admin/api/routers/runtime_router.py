"""
Start/stop/pause/resume/dry-run.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.admin.api.deps import require_admin_token
from src.admin.application.bot_runtime import BotRuntimeService

router = APIRouter(prefix="/api/runtime", tags=["runtime"])


def get_runtime() -> BotRuntimeService:
    return BotRuntimeService.instance()


@router.get("/status", dependencies=[Depends(require_admin_token)])
def status(rt: BotRuntimeService = Depends(get_runtime)) -> dict[str, Any]:
    return rt.status_snapshot()


@router.post("/start", dependencies=[Depends(require_admin_token)])
def start(rt: BotRuntimeService = Depends(get_runtime)) -> dict[str, str]:
    try:
        rt.start()
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/stop", dependencies=[Depends(require_admin_token)])
def stop(rt: BotRuntimeService = Depends(get_runtime)) -> dict[str, str]:
    rt.stop()
    return {"status": "stopped"}


@router.post("/pause", dependencies=[Depends(require_admin_token)])
def pause(rt: BotRuntimeService = Depends(get_runtime)) -> dict[str, str]:
    try:
        rt.pause()
        return {"status": "paused"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/resume", dependencies=[Depends(require_admin_token)])
def resume(rt: BotRuntimeService = Depends(get_runtime)) -> dict[str, str]:
    try:
        rt.resume()
        return {"status": "resumed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/dry-run", dependencies=[Depends(require_admin_token)])
def dry_run(rt: BotRuntimeService = Depends(get_runtime)) -> dict[str, Any]:
    try:
        return rt.run_dry_run_once()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
