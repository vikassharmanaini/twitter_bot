"""
Targets YAML CRUD.
"""

from __future__ import annotations

from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.admin.api.deps import require_admin_token
from src.admin.infrastructure.config_repository import ConfigRepository
from src.config_loader import load_config

router = APIRouter(prefix="/api/targets", tags=["targets"])


class TargetRow(BaseModel):
    username: str
    category: str = ""
    priority: int = Field(default=3, ge=1, le=5)
    enabled: bool = True


def _targets_path(repo: ConfigRepository) -> Any:
    cfg = load_config(repo.path, skip_secret_validation=True)
    from pathlib import Path

    return Path(cfg.paths.targets_file)


@router.get("", dependencies=[Depends(require_admin_token)])
def list_targets(repo: ConfigRepository = Depends(ConfigRepository)) -> dict[str, Any]:
    path = _targets_path(repo)
    if not path.is_file():
        return {"targets": []}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {"targets": raw.get("targets") or []}


@router.put("", dependencies=[Depends(require_admin_token)])
def put_targets(
    body: dict[str, Any],
    repo: ConfigRepository = Depends(ConfigRepository),
) -> dict[str, str]:
    path = _targets_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    if "targets" not in body:
        raise HTTPException(status_code=400, detail="expected { targets: [...] }")
    path.write_text(yaml.safe_dump(body, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return {"status": "ok"}


@router.post("", dependencies=[Depends(require_admin_token)])
def add_target(
    row: TargetRow,
    repo: ConfigRepository = Depends(ConfigRepository),
) -> dict[str, str]:
    path = _targets_path(repo)
    raw: dict[str, Any]
    if path.is_file():
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        raw = {"targets": []}
    targets = list(raw.get("targets") or [])
    h = row.username.lstrip("@")
    targets.append(
        {
            "username": h,
            "category": row.category or "General",
            "priority": row.priority,
            "enabled": row.enabled,
        }
    )
    raw["targets"] = targets
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return {"status": "ok", "username": h}


@router.post("/{handle}/disable", dependencies=[Depends(require_admin_token)])
def disable_target(
    handle: str,
    repo: ConfigRepository = Depends(ConfigRepository),
) -> dict[str, str]:
    path = _targets_path(repo)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="no targets file")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    targets = raw.get("targets") or []
    h = handle.lstrip("@").lower()
    for row in targets:
        if isinstance(row, dict) and str(row.get("username", "")).lstrip("@").lower() == h:
            row["enabled"] = False
    raw["targets"] = targets
    path.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return {"status": "ok"}
