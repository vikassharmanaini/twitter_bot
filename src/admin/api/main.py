"""
FastAPI app: REST + WebSocket + optional static admin UI.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from src.admin.api.connection_manager import ConnectionManager
from src.admin.api.deps import ws_token_ok
from src.admin.api.routers.config_router import router as config_rt
from src.admin.api.routers.data_router import router as data_rt
from src.admin.api.routers.jobs_router import router as jobs_rt
from src.admin.api.routers.runtime_router import router as runtime_rt
from src.admin.api.routers.targets_router import router as targets_rt
from src.admin.application.bot_runtime import BotRuntimeService
from src.admin.infrastructure.log_broadcaster import parse_log_line_for_event

manager = ConnectionManager()
_pump_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pump_task
    rt = BotRuntimeService.instance()

    async def pump() -> None:
        tick = 0
        while True:
            batch = rt.broadcaster.get_nowait_batch(100)
            for line in batch:
                evt = parse_log_line_for_event(line)
                evt["type"] = "log"
                await manager.broadcast_json(evt)
            tick += 1
            if tick >= 40:
                tick = 0
                try:
                    await manager.broadcast_json({"type": "status", "data": rt.status_snapshot()})
                except Exception:
                    pass
            await asyncio.sleep(0.05)

    _pump_task = asyncio.create_task(pump())
    yield
    if _pump_task:
        _pump_task.cancel()
        try:
            await _pump_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Twitter Dev-Bot Admin", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_rt)
app.include_router(runtime_rt)
app.include_router(targets_rt)
app.include_router(data_rt)
app.include_router(jobs_rt)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    if not ws_token_ok(websocket):
        await websocket.close(code=4401)
        return
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


def _admin_dist() -> Path | None:
    root = Path(__file__).resolve().parent.parent.parent.parent
    dist = root / "admin-ui" / "dist"
    if dist.is_dir() and (dist / "index.html").is_file():
        return dist
    return None


_dist_dir = _admin_dist()


if _dist_dir is not None:

    @app.get("/")
    async def spa_index() -> FileResponse:
        return FileResponse(_dist_dir / "index.html")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith(("api/", "docs", "openapi.json", "redoc")):
            raise HTTPException(status_code=404)
        candidate = _dist_dir / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_dist_dir / "index.html")
