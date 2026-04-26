"""Tests for admin API: config repository, health, optional ADMIN_TOKEN."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

from src.admin.api.main import app
from src.admin.api.connection_manager import ConnectionManager
from src.admin.infrastructure.config_repository import ConfigRepository
from src.admin.infrastructure.log_broadcaster import BroadcastLogHandler, LogBroadcaster, parse_log_line_for_event
from tests.fixtures import MINIMAL_CONFIG_DICT, write_config_yaml


def test_health_public() -> None:
    with TestClient(app) as c:
        r = c.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_config_mask_secret_status(tmp_path: Path) -> None:
    p = write_config_yaml(tmp_path / "c.yaml")
    repo = ConfigRepository(p)
    masked, status = repo.mask_for_display()
    assert masked["openrouter"]["api_key"] == ""
    assert status.get("openrouter.api_key") is True


def test_config_save_merges_blank_secret(tmp_path: Path) -> None:
    p = write_config_yaml(tmp_path / "c.yaml")
    repo = ConfigRepository(p)
    body = yaml.safe_load(p.read_text(encoding="utf-8"))
    body["openrouter"]["api_key"] = ""
    body["bot"]["dry_run"] = True
    repo.save(body, allow_incomplete=False, merge_secrets=True)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert raw["openrouter"]["api_key"] == MINIMAL_CONFIG_DICT["openrouter"]["api_key"]


def test_admin_read_apis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_config_yaml(tmp_path / "config.yaml")
    monkeypatch.setenv("BOT_CONFIG", str(tmp_path / "config.yaml"))
    with TestClient(app) as c:
        for path in (
            "/api/targets",
            "/api/replies/recent",
            "/api/db/summary",
            "/api/stats/weekly",
            "/api/stats/performance",
            "/api/runtime/status",
        ):
            r = c.get(path)
            assert r.status_code == 200, path


def test_admin_targets_add(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_config_yaml(tmp_path / "config.yaml")
    monkeypatch.setenv("BOT_CONFIG", str(tmp_path / "config.yaml"))
    # Ensure targets file under tmp data dir
    import yaml

    from src.config_loader import load_config

    cfg = load_config(tmp_path / "config.yaml", skip_secret_validation=True)
    tpath = tmp_path / "targets.yaml"
    tpath.write_text(yaml.safe_dump({"targets": []}), encoding="utf-8")
    # point config at tmp targets — rewrite config
    raw = yaml.safe_load((tmp_path / "config.yaml").read_text(encoding="utf-8"))
    raw.setdefault("paths", {})["targets_file"] = str(tpath)
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")

    with TestClient(app) as c:
        r = c.post("/api/targets", json={"username": "newacc", "category": "x", "priority": 2})
        assert r.status_code == 200
        assert c.get("/api/targets").json()["targets"]


def test_websocket_connect_public_when_no_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_config_yaml(tmp_path / "config.yaml")
    monkeypatch.setenv("BOT_CONFIG", str(tmp_path / "config.yaml"))
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    with TestClient(app) as c:
        with c.websocket_connect("/ws/events") as ws:
            ws.send_text("ping")


def test_log_broadcaster_and_parse() -> None:
    b = LogBroadcaster(maxsize=10)
    b.put_log_line('{"message":"x","level":"INFO"}')
    lines = b.get_nowait_batch(5)
    assert len(lines) == 1
    evt = parse_log_line_for_event(lines[0])
    assert evt.get("message") == "x"


def test_broadcast_log_handler_emits() -> None:
    b = LogBroadcaster(maxsize=10)
    h = BroadcastLogHandler(b)
    log = logging.getLogger("test_admin_broadcast")
    log.setLevel(logging.INFO)
    log.addHandler(h)
    try:
        log.info("hello")
    finally:
        log.removeHandler(h)
    batch = b.get_nowait_batch(5)
    assert batch and "hello" in batch[0]


def test_connection_manager_broadcast() -> None:
    async def _run() -> None:
        m = ConnectionManager()
        ws = MagicMock()
        ws.send_json = AsyncMock(return_value=None)
        m._connections.append(ws)
        await m.broadcast_json({"type": "t"})
        ws.send_json.assert_called_once()

    asyncio.run(_run())


def test_runtime_pause_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_config_yaml(tmp_path / "config.yaml")
    monkeypatch.setenv("BOT_CONFIG", str(tmp_path / "config.yaml"))
    with TestClient(app) as c:
        assert c.post("/api/runtime/pause").status_code == 200
        assert c.post("/api/runtime/resume").status_code == 200


def test_config_bootstrap_post(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "fresh.yaml"
    monkeypatch.setenv("BOT_CONFIG", str(p))
    assert not p.is_file()
    with TestClient(app) as c:
        r = c.post("/api/config/bootstrap")
        assert r.status_code == 200
        assert p.is_file()


def test_config_put_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_config_yaml(tmp_path / "config.yaml")
    monkeypatch.setenv("BOT_CONFIG", str(tmp_path / "config.yaml"))
    raw = yaml.safe_load((tmp_path / "config.yaml").read_text(encoding="utf-8"))
    with TestClient(app) as c:
        r = c.put("/api/config?allow_incomplete=true", json=raw)
        assert r.status_code == 200


def test_targets_disable_route(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_config_yaml(tmp_path / "config.yaml")
    monkeypatch.setenv("BOT_CONFIG", str(tmp_path / "config.yaml"))
    raw = yaml.safe_load((tmp_path / "config.yaml").read_text(encoding="utf-8"))
    tpath = tmp_path / "t.yaml"
    tpath.write_text(yaml.safe_dump({"targets": [{"username": "x", "enabled": True}]}), encoding="utf-8")
    raw.setdefault("paths", {})["targets_file"] = str(tpath)
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    with TestClient(app) as c:
        assert c.post("/api/targets/x/disable").status_code == 200


def test_job_report_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_config_yaml(tmp_path / "config.yaml")
    monkeypatch.setenv("BOT_CONFIG", str(tmp_path / "config.yaml"))
    out = tmp_path / "rep.html"
    with TestClient(app) as c:
        r = c.post("/api/jobs/report", json={"out": str(out)})
        assert r.status_code == 200
        assert out.is_file()


def test_config_get_requires_admin_token_when_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_config_yaml(tmp_path / "config.yaml")
    monkeypatch.setenv("BOT_CONFIG", str(tmp_path / "config.yaml"))
    monkeypatch.setenv("ADMIN_TOKEN", "admin-test-secret")
    with TestClient(app) as c:
        assert c.get("/api/config").status_code == 401
        r = c.get("/api/config", headers={"Authorization": "Bearer admin-test-secret"})
        assert r.status_code == 200
        data = r.json()
        assert "config" in data and "secret_status" in data
