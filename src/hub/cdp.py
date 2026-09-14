from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from hub.config import ROOT


def mcp_server_path() -> Path:
    return ROOT / "vendor" / "tradingview-mcp" / "src" / "server.js"


def desktop_running() -> bool:
    if sys.platform == "win32":
        completed = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq TradingView.exe"],
            capture_output=True,
            text=True,
            check=False,
        )
        return "TradingView.exe" in (completed.stdout or "")
    completed = subprocess.run(["pgrep", "-if", "TradingView"], capture_output=True, check=False)
    return completed.returncode == 0


def probe_cdp(port: int = 9222, timeout: float = 1.5) -> dict[str, Any]:
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {
            "connected": True,
            "port": port,
            "url": url,
            "browser": payload.get("Browser"),
            "webSocketDebuggerUrl": payload.get("webSocketDebuggerUrl"),
        }
    except urllib.error.URLError as exc:
        return {
            "connected": False,
            "port": port,
            "url": url,
            "error": str(exc.reason if getattr(exc, "reason", None) else exc),
        }
    except Exception as exc:  # noqa: BLE001 - surface any probe failure to the setup page
        return {"connected": False, "port": port, "url": url, "error": str(exc)}


def connection_snapshot(port: int = 9222) -> dict[str, Any]:
    cdp = probe_cdp(port)
    app_on = desktop_running()
    if cdp["connected"]:
        state = "ready"
        summary = "TradingView debug 포트에 연결됨. MCP로 차트/백테스트를 읽을 수 있음."
    elif app_on:
        state = "app_without_debug"
        summary = "앱은 켜져 있지만 debug 포트가 닫혀 있음. debug 모드로 다시 실행해야 함."
    else:
        state = "offline"
        summary = "TradingView Desktop이 실행 중이지 않음."
    return {
        "state": state,
        "summary": summary,
        "desktop_running": app_on,
        "mcp_installed": mcp_server_path().exists(),
        "mcp_server": str(mcp_server_path()),
        "cdp": cdp,
    }
