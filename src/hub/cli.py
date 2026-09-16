from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hub.config import DEFAULT_CONFIG, load_config
from hub.ledger import record_from_cycle_file, rewrite_markdown
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


def cmd_record(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    cycle_path = Path(args.from_cycle) if args.from_cycle else (config.runs_dir / "cycles.jsonl")
    ban_match: dict[str, float] = {}
    for item in args.ban or []:
        if "=" not in item:
            raise SystemExit(f"ban must look like name=value, got {item!r}")
        key, value = item.split("=", 1)
        ban_match[key.strip()] = float(value)
    entry = record_from_cycle_file(
        cycle_path,
        config,
        hypothesis=args.hypothesis or "",
        change=args.change or "",
        verdict=args.verdict or "",
        lesson=args.lesson or "",
        ban_match=ban_match or None,
    )
    _print(json.dumps(entry, indent=2, ensure_ascii=True))
    return 0


def cmd_ledger(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    rewrite_markdown(config.ledger_jsonl, config.ledger_md)
    _print(str(config.ledger_md))
    return 0


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

    record = sub.add_parser("record", help="Append the last cycle to ledger.jsonl / ledger.md")
    add_common(record)
    record.add_argument("--from-cycle", help="cycles.jsonl path (default: <runs_dir>/cycles.jsonl)")
    record.add_argument("--hypothesis", default="", help="What this cycle was testing")
    record.add_argument("--change", default="", help="The one code or param change")
    record.add_argument("--verdict", default=None, choices=["keep", "reject", "note"])
    record.add_argument("--lesson", default="", help="Why keep or reject")
    record.add_argument("--ban", action="append", default=[], help="Repeatable name=value to never retry")
    record.set_defaults(func=cmd_record)

    ledger = sub.add_parser("ledger", help="Rebuild ledger.md from ledger.jsonl")
    add_common(ledger)
    ledger.set_defaults(func=cmd_ledger)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
