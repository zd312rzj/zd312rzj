from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator

from douyin_live_danmaku_test import parse_live_id

from .collector import BrowserDanmakuCollector
from .database import DashboardDatabase


@dataclass
class SessionState:
    session_id: int | None = None
    room_id: str | None = None
    source_url: str | None = None
    status: str = "idle"
    error_message: str | None = None
    started_at: str | None = None


class DashboardService:
    def __init__(self, database: DashboardDatabase) -> None:
        self.database = database
        self.state = SessionState()
        self.collector: BrowserDanmakuCollector | None = None
        self.queues: list[asyncio.Queue[str]] = []
        self.lock = threading.Lock()
        self.loop: asyncio.AbstractEventLoop | None = None

    def start_session(self, room: str, headless: bool = False) -> dict[str, Any]:
        self.database.initialize()
        with self.lock:
            if self.collector:
                self.collector.stop()
                self.collector = None
            live_id = parse_live_id(room)
            session_id = self.database.create_session(live_id, room)
            self.state = SessionState(
                session_id=session_id,
                room_id=live_id,
                source_url=room,
                status="starting",
                started_at=datetime.now().isoformat(timespec="seconds"),
            )
            self.collector = BrowserDanmakuCollector(room=room, on_event=self.handle_collector_event, headless=headless)
            self.collector.start()
        self.broadcast({"type": "session", "event": "started", "session": self.current_session()})
        return self.current_session()

    def stop_session(self) -> dict[str, Any]:
        with self.lock:
            collector = self.collector
            self.collector = None
        if collector:
            collector.stop()
        if self.state.session_id:
            self.database.finish_session(self.state.session_id, "stopped")
        self.state.status = "stopped"
        self.broadcast({"type": "session", "event": "stopped", "session": self.current_session()})
        return self.current_session()

    def current_session(self) -> dict[str, Any]:
        return {
            "session_id": self.state.session_id,
            "room_id": self.state.room_id,
            "source_url": self.state.source_url,
            "status": self.state.status,
            "error_message": self.state.error_message,
            "started_at": self.state.started_at,
        }

    def handle_collector_event(self, event: dict[str, Any]) -> None:
        if event.get("type") == "chat" and self.state.session_id:
            stored = self.database.insert_chat(self.state.session_id, event)
            self.state.status = "running"
            self.broadcast({"type": "chat", "message": stored})
            self.broadcast({"type": "stats", "stats": self.database.stats(self.state.session_id)})
            return

        if event.get("type") == "system":
            status_event = event.get("event")
            if status_event == "connected":
                self.state.status = "running"
            elif status_event == "fatal":
                self.state.status = "error"
                self.state.error_message = event.get("message")
                if self.state.session_id:
                    self.database.finish_session(self.state.session_id, "error", self.state.error_message)
            elif status_event == "closed" and self.state.status != "error":
                self.state.status = "stopped"
        self.broadcast({"type": "system", "system": event, "session": self.current_session()})

    def broadcast(self, payload: dict[str, Any]) -> None:
        message = f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        if self.loop and self.loop.is_running():
            for queue in list(self.queues):
                asyncio.run_coroutine_threadsafe(queue.put(message), self.loop)

    async def event_stream(self) -> AsyncGenerator[str, None]:
        self.loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str] = asyncio.Queue()
        self.queues.append(queue)
        await queue.put(f"data: {json.dumps({'type': 'hello', 'session': self.current_session()}, ensure_ascii=False)}\n\n")
        try:
            while True:
                try:
                    yield await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            if queue in self.queues:
                self.queues.remove(queue)
