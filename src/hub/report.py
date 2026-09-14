from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from hub.models import CycleRecord, HubConfig, LoopResult


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_runs_dir(config: HubConfig) -> Path:
    config.runs_dir.mkdir(parents=True, exist_ok=True)
    return config.runs_dir


def cycle_to_dict(record: CycleRecord) -> dict:
    metrics = record.metrics
    return {
        "iteration": record.iteration,
        "params": record.params,
        "accepted": record.accepted,
        "reason": record.reason,
        "score": record.score,
        "pine_snapshot": str(record.pine_snapshot) if record.pine_snapshot else None,
        "metrics": {
            "net_profit_percent": metrics.net_profit_percent,
            "profit_factor": metrics.profit_factor,
            "max_drawdown_percent": metrics.max_drawdown_percent,
            "total_trades": metrics.total_trades,
            "percent_profitable": metrics.percent_profitable,
            "error": metrics.error,
        },
    }


def write_jsonl(path: Path, record: CycleRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(cycle_to_dict(record), ensure_ascii=True) + "\n")


def write_markdown(result: LoopResult, config: HubConfig) -> Path:
    runs = ensure_runs_dir(config)
    path = runs / f"report-{_stamp()}.md"
    best = result.best
    lines = [
        "# Backtest Optimize Report",
        "",
        f"- status: {result.status}",
        f"- symbol: `{config.symbol}`",
        f"- timeframe: `{config.timeframe}`",
        f"- iterations: {result.iterations} / {config.loop_limit}",
        f"- target net profit %: {config.target.net_profit_percent}",
        "",
    ]
    if best:
        lines += [
            "## Best cycle",
            "",
            f"- iteration: {best.iteration}",
            f"- score: {best.score:.3f}",
            f"- reason: {best.reason}",
            f"- params: `{json.dumps(best.params)}`",
            f"- net_profit_percent: {best.metrics.net_profit_percent}",
            f"- profit_factor: {best.metrics.profit_factor}",
            f"- max_drawdown_percent: {best.metrics.max_drawdown_percent}",
            f"- total_trades: {best.metrics.total_trades}",
            "",
        ]
    lines += ["## History", ""]
    for record in result.history:
        lines.append(
            f"- iter {record.iteration}: score={record.score:.2f} "
            f"np%={record.metrics.net_profit_percent} "
            f"pf={record.metrics.profit_factor} "
            f"dd%={record.metrics.max_drawdown_percent} "
            f"trades={record.metrics.total_trades} "
            f"accepted={record.accepted} ({record.reason})"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
