#!/usr/bin/env python3
"""Run the local Douyin live danmaku dashboard."""

from __future__ import annotations

import os
import json
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser


PREFERRED_PYTHON = r"D:\Anaconda3\python.exe"
HOST = "127.0.0.1"
PORT = 8787
URL = f"http://{HOST}:{PORT}/"
DB_ENV_KEYS = (
    "DANMAKU_DB_HOST",
    "DANMAKU_DB_PORT",
    "DANMAKU_DB_USER",
    "DANMAKU_DB_PASSWORD",
    "DANMAKU_DB_NAME",
)


def ensure_python_runtime() -> None:
    current = os.path.abspath(sys.executable).lower()
    preferred = os.path.abspath(PREFERRED_PYTHON).lower()
    if os.path.exists(PREFERRED_PYTHON) and current != preferred:
        print(f"当前Python解释器不是项目使用的环境：{sys.executable}")
        print(f"请在VS Code里选择解释器：{PREFERRED_PYTHON}")
        print(f"或运行：{PREFERRED_PYTHON} {os.path.abspath(__file__)}")
        input("按回车退出")
        raise SystemExit(1)


def load_windows_user_env() -> None:
    if os.name != "nt":
        return
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env_key:
            for key in DB_ENV_KEYS:
                if os.getenv(key):
                    continue
                try:
                    value, _ = winreg.QueryValueEx(env_key, key)
                except FileNotFoundError:
                    continue
                os.environ[key] = str(value)
    except OSError:
        return


def ensure_mysql_env() -> None:
    os.environ.setdefault("DANMAKU_DB_HOST", "127.0.0.1")
    os.environ.setdefault("DANMAKU_DB_PORT", "3306")
    os.environ.setdefault("DANMAKU_DB_USER", "root")
    os.environ.setdefault("DANMAKU_DB_NAME", "douyin_danmaku")
    if os.getenv("DANMAKU_DB_PASSWORD"):
        return

    print("没有读取到MySQL密码，所以程序会用空密码连接。")
    print("请先设置Windows用户环境变量 DANMAKU_DB_PASSWORD，然后重新运行。")
    input("按回车退出")
    raise SystemExit(1)


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def existing_server_has_empty_password_error() -> bool:
    try:
        with urllib.request.urlopen(f"{URL}api/stats", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False
    error = str(payload.get("db_error", ""))
    return "using password: NO" in error


def restart_stale_dashboard_if_needed() -> bool:
    if not is_port_open(HOST, PORT) or not existing_server_has_empty_password_error():
        return False

    script_path = os.path.abspath(__file__).lower()
    for pid in find_listening_pids(PORT):
        command_line = process_command_line(pid).lower()
        if script_path not in command_line:
            continue
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False, capture_output=True)
        for _ in range(20):
            if not is_port_open(HOST, PORT):
                return True
            time.sleep(0.2)
    return False


def find_listening_pids(port: int) -> set[int]:
    try:
        output = subprocess.check_output(
            ["netstat", "-ano"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        return set()

    pids: set[int] = set()
    suffix = f":{port}"
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0] == "TCP" and parts[1].endswith(suffix) and parts[3] == "LISTENING":
            try:
                pids.add(int(parts[-1]))
            except ValueError:
                continue
    return pids


def process_command_line(pid: int) -> str:
    if os.name != "nt":
        return ""
    command = (
        "Get-CimInstance Win32_Process -Filter "
        f"'ProcessId={pid}' | Select-Object -ExpandProperty CommandLine"
    )
    try:
        return subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", command],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        return ""


def open_browser_later() -> None:
    for _ in range(30):
        if is_port_open(HOST, PORT):
            webbrowser.open(URL)
            return
        time.sleep(0.2)


def ensure_dependencies() -> None:
    try:
        import uvicorn  # noqa: F401
    except ModuleNotFoundError:
        print("缺少依赖：uvicorn")
        print("请运行：python -m pip install -r requirements.txt")
        input("按回车退出")
        raise SystemExit(1)


if __name__ == "__main__":
    ensure_python_runtime()
    load_windows_user_env()
    ensure_mysql_env()
    ensure_dependencies()
    import uvicorn

    restart_stale_dashboard_if_needed()

    if is_port_open(HOST, PORT):
        webbrowser.open(URL)
    else:
        threading.Thread(target=open_browser_later, daemon=True).start()
        uvicorn.run("dashboard_app.api:app", host=HOST, port=PORT, reload=False)
