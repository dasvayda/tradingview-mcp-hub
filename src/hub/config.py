from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from hub.models import HubConfig, MutationSpec, PineSpec, TargetSpec, TvSpec

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config" / "default.yaml"


def _as_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path)


def _resolve_command(root: Path, parts: list[str]) -> tuple[str, ...]:
    resolved: list[str] = []
    for part in parts:
        candidate = root / part
        resolved.append(str(candidate) if candidate.exists() else part)
    return tuple(resolved)


def _knobs(raw: dict[str, Any]) -> dict[str, tuple[float, ...]]:
    knobs: dict[str, tuple[float, ...]] = {}
    for name, values in (raw or {}).items():
        knobs[str(name)] = tuple(float(v) for v in values)
    return knobs


def load_config(path: str | Path | None = None) -> HubConfig:
    config_path = Path(path) if path else DEFAULT_CONFIG
    if not config_path.is_absolute():
        config_path = (Path.cwd() / config_path).resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    root = ROOT

    target = raw.get("target") or {}
    pine = raw.get("pine") or {}
    tv = raw.get("tv") or {}
    mutation = raw.get("mutation") or {}
    output = raw.get("output") or {}

    command = tv.get("command") or ["tv"]
    if isinstance(command, str):
        command = [command]

    mode = str(mutation.get("mode") or "params").lower()
    if mode not in {"params", "agent"}:
        raise ValueError(f"mutation.mode must be 'params' or 'agent', got {mode!r}")

    loop_limit = int(raw.get("loop_limit", 20))
    if loop_limit < 1:
        raise ValueError("loop_limit must be >= 1")

    layout_name = str(raw.get("layout") or "").strip() or None
    ledger = raw.get("ledger") or {}

    return HubConfig(
        symbol=str(raw.get("symbol") or "BINANCE:DOGEUSDT"),
        timeframe=str(raw.get("timeframe") or "60"),
        layout=layout_name,
        loop_limit=loop_limit,
        initial_capital=float(raw.get("initial_capital", 10000)),
        target=TargetSpec(
            net_profit_percent=float(target.get("net_profit_percent", 20)),
            min_trades=int(target.get("min_trades", 20)),
            min_profit_factor=float(target.get("min_profit_factor", 1.2)),
            max_drawdown_percent=float(target.get("max_drawdown_percent", 35)),
        ),
        pine=PineSpec(
            source_path=_as_path(root, pine.get("source_path") or "pinescript/doge_daily_ma_reclaim.pine"),
            current_path=_as_path(root, pine.get("current_path") or "pinescript/current.pine"),
        ),
        tv=TvSpec(
            command=_resolve_command(root, [str(part) for part in command]),
            cdp_port=int(tv.get("cdp_port", 9222)),
            compile_wait_seconds=float(tv.get("compile_wait_seconds", 6)),
            results_wait_seconds=float(tv.get("results_wait_seconds", 10)),
            results_retries=int(tv.get("results_retries", 6)),
            screenshot=bool(tv.get("screenshot", False)),
            clear_existing_strategies=bool(tv.get("clear_existing_strategies", True)),
            keep_strategy_substring=str(tv.get("keep_strategy_substring") or "HUB DOGE"),
        ),
        mutation=MutationSpec(
            mode=mode,
            seed=int(mutation.get("seed", 7)),
            knobs=_knobs(mutation.get("knobs") or {}),
        ),
        runs_dir=_as_path(root, output.get("runs_dir") or "runs"),
        ledger_jsonl=_as_path(root, ledger.get("jsonl") or "ledger.jsonl"),
        ledger_md=_as_path(root, ledger.get("markdown") or "ledger.md"),
        root=root,
        raw=raw,
    )
