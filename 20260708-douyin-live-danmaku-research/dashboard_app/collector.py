from __future__ import annotations

import threading
import time
from typing import Any, Callable

from douyin_live_danmaku_test import DEFAULT_USER_AGENT, decode_frame, frame_preview, parse_live_id


EventCallback = Callable[[dict[str, Any]], None]


class BrowserDanmakuCollector:
    def __init__(
        self,
        room: str,
        on_event: EventCallback,
        headless: bool = False,
        browser_timeout: int = 30,
    ) -> None:
        self.room = room
        self.on_event = on_event
        self.headless = headless
        self.browser_timeout = browser_timeout
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.live_id = parse_live_id(room)

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run, name="danmaku-collector", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=8)

    def _emit(self, event: dict[str, Any]) -> None:
        self.on_event(event)

    def _run(self) -> None:
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            self._emit(
                {
                    "type": "system",
                    "event": "fatal",
                    "message": "缺少Playwright，请运行python -m pip install -r requirements.txt，并执行python -m playwright install chromium",
                    "detail": str(exc),
                }
            )
            return

        state = {"ws_captured": False, "frames": 0, "decode_errors": 0, "chats": 0, "last_status": time.time()}
        live_url = f"https://live.douyin.com/{self.live_id}"

        def emit_frame(payload: Any) -> None:
            state["frames"] += 1
            try:
                events, _ack, live_ended = decode_frame(payload, False)
                for event in events:
                    if event.get("type") == "chat":
                        state["chats"] += 1
                    self._emit(event)
                if live_ended:
                    self.stop_event.set()
            except Exception as exc:
                state["decode_errors"] += 1
                if state["decode_errors"] == 1:
                    self._emit(
                        {
                            "type": "system",
                            "event": "decode_error",
                            "message": "浏览器收到数据，但暂时无法解析，会继续监听",
                            "detail": {"error": str(exc), "frame": frame_preview(payload)},
                        }
                    )

        self._emit({"type": "system", "event": "browser_opening", "message": "正在打开浏览器监听直播间"})
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=DEFAULT_USER_AGENT,
                    viewport={"width": 1365, "height": 768},
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai",
                )
                page = context.new_page()

                def on_websocket(ws: Any) -> None:
                    url = getattr(ws, "url", "")
                    if "/webcast/im/push/v2/" not in url:
                        return
                    state["ws_captured"] = True
                    self._emit({"type": "system", "event": "connected", "message": "已连接直播间WebSocket"})
                    ws.on("framereceived", emit_frame)

                page.on("websocket", on_websocket)
                page.goto(live_url, wait_until="domcontentloaded", timeout=self.browser_timeout * 1000)

                deadline = time.time() + self.browser_timeout
                while time.time() < deadline and not state["ws_captured"] and not self.stop_event.is_set():
                    page.wait_for_timeout(500)

                if not state["ws_captured"]:
                    raise RuntimeError("没有抓到直播间WebSocket，请确认房间正在直播，或浏览器里没有验证码、登录页、地区限制")

                while not self.stop_event.is_set():
                    page.wait_for_timeout(1000)
                    now = time.time()
                    if now - state["last_status"] >= 15:
                        state["last_status"] = now
                        self._emit(
                            {
                                "type": "system",
                                "event": "listening",
                                "message": "仍在监听",
                                "frames": state["frames"],
                                "decode_errors": state["decode_errors"],
                                "chats": state["chats"],
                            }
                        )
                browser.close()
                self._emit({"type": "system", "event": "closed", "message": "监听已停止"})
        except PlaywrightTimeoutError as exc:
            self._emit({"type": "system", "event": "fatal", "message": "打开直播间超时", "detail": str(exc)})
        except Exception as exc:
            self._emit({"type": "system", "event": "fatal", "message": str(exc)})
