from __future__ import annotations

import argparse
import json
import sys

from hub.config import DEFAULT_CONFIG, load_config
from hub.loop import build_client
from hub.report import cycle_to_dict
from hub.web import serve


def _print(message: str) -> None:
    print(message, flush=True)


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    _, loop = build_client(config, dry_run=args.dry_run)
    result = loop.run(progress=_print)
    payload = {
        "status": result.status,
        "iterations": result.iterations,
        "report": str(result.report_path) if result.report_path else None,
        "best": cycle_to_dict(result.best, config) if result.best else None,
    }
    _print(json.dumps(payload, indent=2))
    return 0 if result.status in {"target_hit", "awaiting_agent_edit"} else 2


def cmd_status(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.dry_run:
        _, loop = build_client(config, dry_run=True)
        health = loop.client.health()
        _print(json.dumps({"dry_run": True, "health": health, "symbol": config.symbol}, indent=2))
        return 0
    from hub.cdp import connection_snapshot

    snapshot = connection_snapshot(config.tv.cdp_port)
    _print(json.dumps({"dry_run": False, "symbol": config.symbol, **snapshot}, indent=2, ensure_ascii=False))
    return 0 if snapshot["state"] == "ready" else 2


def cmd_web(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    serve(args.host, args.port, config.tv.cdp_port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tvhub", description="TradingView MCP backtest optimize hub")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(target: argparse.ArgumentParser) -> None:
        target.add_argument("--config", default=str(DEFAULT_CONFIG), help="YAML config path")
        target.add_argument("--dry-run", action="store_true", help="Mock TradingView results")

    run = sub.add_parser("run", help="Inject Pine, backtest, and loop toward the target")
    add_common(run)
    run.set_defaults(func=cmd_run)
    status = sub.add_parser("status", help="Check TradingView debug port / dry-run connectivity")
    add_common(status)
    status.set_defaults(func=cmd_status)
    web = sub.add_parser("web", help="Open the local TradingView setup page")
    web.add_argument("--config", default=str(DEFAULT_CONFIG), help="YAML config path")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8788)
    web.set_defaults(func=cmd_web)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
