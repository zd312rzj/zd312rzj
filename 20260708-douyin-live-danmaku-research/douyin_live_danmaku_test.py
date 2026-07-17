#!/usr/bin/env python3
"""
Douyin live danmaku local PoC.

Usage:
  python douyin_live_danmaku_test.py
  python douyin_live_danmaku_test.py 123456
  python douyin_live_danmaku_test.py 123456 --headless
  python douyin_live_danmaku_test.py 123456 --sign-url http://127.0.0.1:8787/sign
  python douyin_live_danmaku_test.py 123456 --wss "wss://...&signature=..."

By default this script opens a real browser, captures the signed WSS URL created
by the Douyin live page, then connects to that WSS URL.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import os
import signal
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

try:
    import websocket
except ImportError:
    print(
        json.dumps(
            {
                "type": "system",
                "event": "missing_dependency",
                "message": "缺少依赖，请先运行：python -m pip install websocket-client",
            },
            ensure_ascii=False,
        )
    )
    sys.exit(1)


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


@dataclass
class SignedConnection:
    wss_url: str
    headers: dict[str, str]
    room_id: str | None = None
    title: str | None = None
    heartbeat_interval_ms: int = 5000
    heartbeat_payload: bytes = b"\x3a\x02hb"


class ProtoReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def eof(self) -> bool:
        return self.pos >= len(self.data)

    def read_varint(self) -> int:
        shift = 0
        result = 0
        while True:
            if self.pos >= len(self.data):
                raise ValueError("protobuf varint truncated")
            byte = self.data[self.pos]
            self.pos += 1
            result |= (byte & 0x7F) << shift
            if not byte & 0x80:
                return result
            shift += 7
            if shift > 70:
                raise ValueError("protobuf varint too long")

    def read_bytes(self) -> bytes:
        size = self.read_varint()
        end = self.pos + size
        if end > len(self.data):
            raise ValueError("protobuf bytes truncated")
        value = self.data[self.pos : end]
        self.pos = end
        return value

    def skip(self, wire_type: int) -> None:
        if wire_type == 0:
            self.read_varint()
            return
        if wire_type == 1:
            self.pos += 8
            return
        if wire_type == 2:
            self.read_bytes()
            return
        if wire_type == 5:
            self.pos += 4
            return
        raise ValueError(f"unsupported protobuf wire type: {wire_type}")


def parse_message(data: bytes) -> dict[int, list[Any]]:
    reader = ProtoReader(data)
    fields: dict[int, list[Any]] = {}
    while not reader.eof():
        tag = reader.read_varint()
        field_number = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 0:
            value: Any = reader.read_varint()
        elif wire_type == 1:
            value = reader.data[reader.pos : reader.pos + 8]
            reader.pos += 8
        elif wire_type == 2:
            value = reader.read_bytes()
        elif wire_type == 5:
            value = reader.data[reader.pos : reader.pos + 4]
            reader.pos += 4
        else:
            reader.skip(wire_type)
            continue
        fields.setdefault(field_number, []).append(value)
    return fields


def encode_varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def encode_field_varint(field_number: int, value: int) -> bytes:
    return encode_varint((field_number << 3) | 0) + encode_varint(value)


def encode_field_bytes(field_number: int, value: bytes) -> bytes:
    return encode_varint((field_number << 3) | 2) + encode_varint(len(value)) + value


def text(value: Any) -> str | None:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return None


def first(fields: dict[int, list[Any]], field_number: int) -> Any:
    values = fields.get(field_number)
    return values[0] if values else None


def parse_push_frame(data: bytes) -> dict[str, Any]:
    fields = parse_message(data)
    return {
        "log_id": first(fields, 2) or 0,
        "payload_encoding": text(first(fields, 6)) or "",
        "payload_type": text(first(fields, 7)) or "",
        "payload": first(fields, 8) or b"",
    }


def normalize_frame_data(data: Any) -> bytes:
    if isinstance(data, str):
        try:
            raw = base64.b64decode(data, validate=True)
        except Exception:
            raw = data.encode("latin-1", errors="replace")
    else:
        raw = bytes(data)

    if raw.startswith(b"\x1f\x8b"):
        return gzip.decompress(raw)

    return raw


def parse_response(payload: bytes) -> dict[str, Any]:
    fields = parse_message(payload)
    messages = [parse_webcast_message(item) for item in fields.get(1, []) if isinstance(item, bytes)]
    return {
        "messages": messages,
        "internal_ext": text(first(fields, 5)) or "",
        "need_ack": bool(first(fields, 9) or 0),
    }


def parse_webcast_message(payload: bytes) -> dict[str, Any]:
    fields = parse_message(payload)
    return {
        "method": text(first(fields, 1)) or "unknown",
        "payload": first(fields, 2) or b"",
        "msg_id": str(first(fields, 3) or ""),
    }


def parse_common(payload: bytes | None) -> dict[str, Any]:
    if not payload:
        return {}
    fields = parse_message(payload)
    return {
        "room_id": str(first(fields, 3) or ""),
        "create_time": first(fields, 4),
    }


def parse_user(payload: bytes | None) -> dict[str, Any]:
    if not payload:
        return {}
    fields = parse_message(payload)
    return {
        "id": str(first(fields, 1) or ""),
        "nickname": text(first(fields, 3)) or "",
        "id_str": text(first(fields, 1028)) or "",
    }


def parse_chat_event(payload: bytes, method: str) -> dict[str, Any]:
    fields = parse_message(payload)
    common = parse_common(first(fields, 1))
    user = parse_user(first(fields, 2))
    content = text(first(fields, 3)) or ""
    event_time = first(fields, 15) or common.get("create_time")
    return {
        "type": "chat",
        "room_id": common.get("room_id") or None,
        "user_id": user.get("id_str") or user.get("id") or None,
        "nickname": user.get("nickname") or None,
        "content": content,
        "timestamp": event_time,
        "method": method,
    }


def parse_emoji_chat_event(payload: bytes, method: str) -> dict[str, Any]:
    fields = parse_message(payload)
    common = parse_common(first(fields, 1))
    user = parse_user(first(fields, 2))
    content = text(first(fields, 5)) or "[emoji]"
    return {
        "type": "chat",
        "room_id": common.get("room_id") or None,
        "user_id": user.get("id_str") or user.get("id") or None,
        "nickname": user.get("nickname") or None,
        "content": content,
        "timestamp": common.get("create_time"),
        "method": method,
    }


def parse_control_status(payload: bytes) -> int | None:
    fields = parse_message(payload)
    status = first(fields, 2)
    return int(status) if status is not None else None


def build_ack(log_id: int, internal_ext: str) -> bytes:
    return b"".join(
        [
            encode_field_varint(2, int(log_id)),
            encode_field_bytes(7, b"ack"),
            encode_field_bytes(8, internal_ext.encode("utf-8")),
        ]
    )


def decode_frame(data: bytes, show_unknown: bool) -> tuple[list[dict[str, Any]], bytes | None, bool]:
    frame_data = normalize_frame_data(data)
    frame = parse_push_frame(frame_data)
    payload = frame["payload"]
    if frame["payload_encoding"] == "gzip" or payload.startswith(b"\x1f\x8b"):
        payload = gzip.decompress(payload)

    response = parse_response(payload)
    events: list[dict[str, Any]] = []
    live_ended = False

    for message in response["messages"]:
        method = message["method"]
        body = message["payload"]
        try:
            if method == "WebcastChatMessage":
                events.append(parse_chat_event(body, method))
            elif method == "WebcastEmojiChatMessage":
                events.append(parse_emoji_chat_event(body, method))
            elif method == "WebcastControlMessage":
                if parse_control_status(body) == 3:
                    live_ended = True
                    events.append(
                        {
                            "type": "system",
                            "event": "live_ended",
                            "message": "直播间已结束",
                        }
                    )
            elif show_unknown:
                events.append({"type": "unknown", "method": method, "msg_id": message["msg_id"]})
        except Exception as exc:
            events.append(
                {
                    "type": "system",
                    "event": "message_parse_error",
                    "message": f"{method}解析失败",
                    "detail": str(exc),
                }
            )

    ack = build_ack(frame["log_id"], response["internal_ext"]) if response["need_ack"] else None
    return events, ack, live_ended


def frame_preview(data: Any) -> dict[str, Any]:
    if isinstance(data, str):
        try:
            raw = base64.b64decode(data, validate=True)
            kind = "base64-text"
        except Exception:
            raw = data.encode("latin-1", errors="replace")
            kind = "text"
    else:
        raw = bytes(data)
        kind = "binary"

    preview: dict[str, Any] = {
        "kind": kind,
        "length": len(raw),
        "head_hex": raw[:16].hex(),
    }

    try:
        frame = parse_push_frame(normalize_frame_data(data))
        payload = frame["payload"]
        preview["payload_encoding"] = frame["payload_encoding"]
        preview["payload_type"] = frame["payload_type"]
        preview["payload_length"] = len(payload)
        preview["payload_head_hex"] = payload[:16].hex()
    except Exception:
        pass

    return preview


def parse_live_id(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("房间号为空")
    if value.isdigit():
        return value
    parsed = urllib.parse.urlparse(value)
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        raise ValueError("没有从URL里解析到房间号")
    return parts[-1]


def get_signed_connection(live_id: str, args: argparse.Namespace) -> SignedConnection:
    headers = {"user-agent": DEFAULT_USER_AGENT}
    if args.cookie:
        headers["cookie"] = args.cookie

    if args.wss:
        return SignedConnection(wss_url=args.wss, headers=headers)

    sign_url = args.sign_url or os.getenv("DOUYIN_SIGN_URL")
    if not sign_url:
        return capture_signed_connection_with_browser(live_id, args)

    payload = json.dumps({"liveId": live_id, "cookie": args.cookie}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        sign_url,
        data=payload,
        method="POST",
        headers={"content-type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"签名服务不可用：{sign_url}。请启动本地签名服务，或用 --wss 传入已签名WSS"
        ) from exc

    wss_url = body.get("wssUrl") or body.get("url")
    if not isinstance(wss_url, str) or not wss_url.startswith("wss://"):
        raise RuntimeError("签名服务没有返回有效的wssUrl")

    response_headers = body.get("headers") or {}
    if isinstance(response_headers, dict):
        headers.update({str(k): str(v) for k, v in response_headers.items()})

    heartbeat = body.get("heartbeat") if isinstance(body.get("heartbeat"), dict) else {}
    interval_ms = int(heartbeat.get("intervalMs") or 5000)
    payload_hex = heartbeat.get("payloadHex")
    heartbeat_payload = bytes.fromhex(payload_hex) if isinstance(payload_hex, str) else b"\x3a\x02hb"

    return SignedConnection(
        wss_url=wss_url,
        headers=headers,
        room_id=str(body.get("roomId") or "") or None,
        title=str(body.get("title") or "") or None,
        heartbeat_interval_ms=interval_ms,
        heartbeat_payload=heartbeat_payload,
    )


def capture_signed_connection_with_browser(live_id: str, args: argparse.Namespace) -> SignedConnection:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "缺少自动获取WSS所需依赖。请运行：python -m pip install playwright websocket-client，然后运行：python -m playwright install chromium"
        ) from exc

    live_url = f"https://live.douyin.com/{live_id}"
    timeout_ms = int(args.browser_timeout) * 1000
    captured: dict[str, str] = {}

    print_event(
        {
            "type": "system",
            "event": "browser_opening",
            "message": "正在打开浏览器获取直播间连接地址",
        }
    )

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=args.headless)
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1365, "height": 768},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )
            page = context.new_page()

            def on_websocket(ws: Any) -> None:
                url = getattr(ws, "url", "")
                if "/webcast/im/push/v2/" in url and url.startswith("wss://"):
                    captured["wss_url"] = url

            page.on("websocket", on_websocket)
            page.goto(live_url, wait_until="domcontentloaded", timeout=timeout_ms)

            deadline = time.time() + int(args.browser_timeout)
            while time.time() < deadline and "wss_url" not in captured:
                page.wait_for_timeout(500)

            if "wss_url" not in captured:
                raise RuntimeError(
                    "没有抓到直播间WSS。确认房间号正在直播；如果浏览器里出现验证码、登录页或地区限制，请手动处理后重试"
                )

            cookies = context.cookies("https://live.douyin.com")
            cookie_header = "; ".join(f"{item['name']}={item['value']}" for item in cookies)
            title = page.title()
            browser.close()
    except PlaywrightTimeoutError as exc:
        raise RuntimeError("打开直播间超时，确认网络能访问抖音直播页") from exc

    headers = {"user-agent": DEFAULT_USER_AGENT}
    if cookie_header:
        headers["cookie"] = cookie_header

    print_event(
        {
            "type": "system",
            "event": "wss_captured",
            "message": "已获取直播间连接地址，开始连接弹幕服务",
        }
    )

    return SignedConnection(
        wss_url=captured["wss_url"],
        headers=headers,
        room_id=live_id,
        title=title,
    )


def print_event(event: dict[str, Any]) -> None:
    print(json.dumps(event, ensure_ascii=False), flush=True)


def listen(live_id: str, connection: SignedConnection, args: argparse.Namespace) -> None:
    stopped = threading.Event()

    def handle_signal(_signum: int, _frame: Any) -> None:
        stopped.set()

    signal.signal(signal.SIGINT, handle_signal)
    print_event(
        {
            "type": "system",
            "event": "connecting",
            "message": f"连接直播间 {connection.room_id or live_id}",
        }
    )

    ws = websocket.WebSocket()
    header = [f"{key}: {value}" for key, value in connection.headers.items()]
    ws.connect(connection.wss_url, header=header, timeout=15)
    print_event({"type": "system", "event": "connected", "message": "WebSocket已连接"})

    def heartbeat() -> None:
        while not stopped.is_set():
            time.sleep(connection.heartbeat_interval_ms / 1000)
            try:
                ws.ping(connection.heartbeat_payload)
            except Exception:
                stopped.set()
                return

    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()

    decode_error_count = 0
    try:
        while not stopped.is_set():
            opcode, data = ws.recv_data()
            if opcode not in (websocket.ABNF.OPCODE_BINARY, websocket.ABNF.OPCODE_CONT):
                continue
            try:
                events, ack, live_ended = decode_frame(data, args.unknown)
            except Exception as exc:
                decode_error_count += 1
                if decode_error_count > 1 and not args.unknown:
                    continue
                event: dict[str, Any] = {
                    "type": "system",
                    "event": "decode_error",
                    "message": "收到一个暂时无法解析的数据包，继续等待后续弹幕",
                }
                if args.unknown:
                    event["detail"] = {
                        "error": str(exc),
                        "frame": frame_preview(data),
                    }
                print_event(event)
                continue
            if ack:
                ws.send_binary(ack)
            for event in events:
                print_event(event)
            if live_ended:
                stopped.set()
    finally:
        ws.close()
        print_event({"type": "system", "event": "closed", "message": "连接已关闭"})


def listen_with_browser(live_id: str, args: argparse.Namespace) -> None:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "缺少自动监听所需依赖。请运行：python -m pip install -r requirements.txt，然后运行：python -m playwright install chromium"
        ) from exc

    live_url = f"https://live.douyin.com/{live_id}"
    timeout_ms = int(args.browser_timeout) * 1000
    stopped = threading.Event()
    state = {
        "ws_captured": False,
        "frames": 0,
        "decode_errors": 0,
        "chats": 0,
        "last_status": time.time(),
    }

    def handle_signal(_signum: int, _frame: Any) -> None:
        stopped.set()

    def emit_frame(payload: Any) -> None:
        state["frames"] += 1
        try:
            events, _ack, live_ended = decode_frame(payload, args.unknown)
            for event in events:
                if event.get("type") == "chat":
                    state["chats"] += 1
                print_event(event)
            if live_ended:
                stopped.set()
        except Exception as exc:
            state["decode_errors"] += 1
            if state["decode_errors"] == 1 or args.unknown:
                print_event(
                    {
                        "type": "system",
                        "event": "decode_error",
                        "message": "浏览器收到数据，但脚本暂时无法解析。会继续监听",
                        "detail": {
                            "error": str(exc),
                            "frame": frame_preview(payload),
                        },
                    }
                )

    signal.signal(signal.SIGINT, handle_signal)
    print_event(
        {
            "type": "system",
            "event": "browser_opening",
            "message": "正在打开浏览器并直接监听直播间WebSocket",
        }
    )

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=args.headless)
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
                print_event(
                    {
                        "type": "system",
                        "event": "connected",
                        "message": "已连接直播间WebSocket，正在等待弹幕",
                    }
                )
                ws.on("framereceived", emit_frame)

            page.on("websocket", on_websocket)
            page.goto(live_url, wait_until="domcontentloaded", timeout=timeout_ms)

            deadline = time.time() + int(args.browser_timeout)
            while time.time() < deadline and not state["ws_captured"]:
                page.wait_for_timeout(500)

            if not state["ws_captured"]:
                raise RuntimeError(
                    "没有抓到直播间WebSocket。确认房间正在直播；如果浏览器里出现验证码、登录页或地区限制，请手动处理后重试"
                )

            while not stopped.is_set():
                page.wait_for_timeout(1000)
                now = time.time()
                if now - state["last_status"] >= 15:
                    state["last_status"] = now
                    print_event(
                        {
                            "type": "system",
                            "event": "listening",
                            "message": "仍在监听。直播间没人发言时不会有chat输出",
                            "frames": state["frames"],
                            "decode_errors": state["decode_errors"],
                            "chats": state["chats"],
                        }
                    )

            browser.close()
            print_event({"type": "system", "event": "closed", "message": "浏览器监听已停止"})
    except PlaywrightTimeoutError as exc:
        raise RuntimeError("打开直播间超时，确认网络能访问抖音直播页") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="抖音直播弹幕Python本地测试脚本")
    parser.add_argument("room", nargs="?", help="房间号或直播间URL。不传会进入输入提示")
    parser.add_argument("--sign-url", help="可选签名服务地址。不传时自动打开浏览器获取WSS")
    parser.add_argument("--wss", help="已签名的WebSocket地址")
    parser.add_argument("--cookie", help="可选Cookie，只从命令行传入，不写入文件")
    parser.add_argument("--unknown", action="store_true", help="打印未知消息类型")
    parser.add_argument("--headless", action="store_true", help="用无头浏览器获取WSS，默认会打开可见浏览器")
    parser.add_argument("--browser-timeout", default="30", help="浏览器等待WSS的最长秒数，默认30")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    room = args.room or input("请输入抖音直播间房间号或URL：").strip()
    try:
        live_id = parse_live_id(room)
        if not args.wss and not args.sign_url:
            listen_with_browser(live_id, args)
            return 0
        connection = get_signed_connection(live_id, args)
        listen(live_id, connection, args)
        return 0
    except KeyboardInterrupt:
        print_event({"type": "system", "event": "stopped", "message": "已停止"})
        return 0
    except Exception as exc:
        print_event({"type": "system", "event": "fatal", "message": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
