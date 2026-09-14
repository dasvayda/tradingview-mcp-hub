from __future__ import annotations

import json
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from hub.cdp import connection_snapshot

ASSETS = Path(__file__).resolve().parent / "web_assets"


class SetupHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, cdp_port: int = 9222, **kwargs: Any) -> None:
        self.cdp_port = cdp_port
        super().__init__(*args, directory=str(ASSETS), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self.path = "/index.html"
            return super().do_GET()
        if path == "/api/status":
            body = json.dumps(connection_snapshot(self.cdp_port), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404, "Not found")


def serve(host: str, port: int, cdp_port: int) -> None:
    handler = partial(SetupHandler, cdp_port=cdp_port)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"TradingView setup page: http://{host}:{port}", flush=True)
    print("Stop with Ctrl+C", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        httpd.server_close()
