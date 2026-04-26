"""
Config read (masked) and write (validated YAML).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.admin.api.deps import require_admin_token
from src.admin.infrastructure.config_repository import ConfigRepository

router = APIRouter(prefix="/api/config", tags=["config"])


def get_repo() -> ConfigRepository:
    return ConfigRepository()


@router.get("", dependencies=[Depends(require_admin_token)])
def get_config(repo: ConfigRepository = Depends(get_repo)) -> dict[str, Any]:
    try:
        masked, secret_status = repo.mask_for_display()
        return {"config": masked, "secret_status": secret_status}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("", dependencies=[Depends(require_admin_token)])
def put_config(
    body: dict[str, Any],
    allow_incomplete: bool = Query(False),
    repo: ConfigRepository = Depends(get_repo),
) -> dict[str, str]:
    try:
        repo.save(body, allow_incomplete=allow_incomplete, merge_secrets=True)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/bootstrap", dependencies=[Depends(require_admin_token)])
def bootstrap_config(repo: ConfigRepository = Depends(get_repo)) -> dict[str, str]:
    try:
        repo.bootstrap_from_example()
        return {"status": "ok", "path": str(repo.path)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
