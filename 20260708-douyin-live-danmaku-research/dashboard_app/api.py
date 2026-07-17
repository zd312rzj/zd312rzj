from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .database import DashboardDatabase, iso_or_none
from .service import DashboardService


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

database = DashboardDatabase()
service = DashboardService(database)
app = FastAPI(title="Douyin Live Danmaku Dashboard")
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


class StartSessionRequest(BaseModel):
    room: str
    headless: bool = False


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/session/start")
def start_session(payload: StartSessionRequest) -> dict[str, Any]:
    try:
        return service.start_session(payload.room, payload.headless)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"MySQL初始化失败：{exc}") from exc


@app.post("/api/session/stop")
def stop_session() -> dict[str, Any]:
    return service.stop_session()


@app.get("/api/session/current")
def current_session() -> dict[str, Any]:
    return service.current_session()


@app.get("/api/messages")
def latest_messages(limit: int = Query(default=200, ge=1, le=500)) -> list[dict[str, Any]]:
    try:
        return database.latest_messages(service.state.session_id, limit)
    except Exception:
        return []


@app.get("/api/stats")
def stats() -> dict[str, Any]:
    try:
        return database.stats(service.state.session_id)
    except Exception as exc:
        return {
            "total_messages": 0,
            "last_minute_messages": 0,
            "active_users": 0,
            "keyword_hits": 0,
            "trend": [],
            "keywords": [],
            "db_error": str(exc),
        }


@app.get("/api/ranking/users")
def user_ranking(limit: int = Query(default=10, ge=1, le=50)) -> list[dict[str, Any]]:
    try:
        return database.user_ranking(service.state.session_id, limit)
    except Exception:
        return []


@app.get("/api/export/messages.csv")
def export_messages() -> Response:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["received_at", "event_time", "room_id", "user_id", "nickname", "content", "method"])
    try:
        rows = database.export_messages(service.state.session_id)
    except Exception as exc:
        rows = []
        writer.writerow(["", "", "", "", "MySQL连接失败", str(exc), ""])
    for row in rows:
        writer.writerow(
            [
                iso_or_none(row.get("received_at")),
                iso_or_none(row.get("event_time")),
                row.get("room_id") or "",
                row.get("user_id") or "",
                row.get("nickname") or "",
                row.get("content") or "",
                row.get("method") or "",
            ]
        )
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=danmaku_messages.csv"},
    )


@app.get("/api/events")
async def events() -> StreamingResponse:
    return StreamingResponse(service.event_stream(), media_type="text/event-stream")
