from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from hub.metrics import analysis_snapshot
from hub.models import CycleRecord, HubConfig, LoopResult


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_runs_dir(config: HubConfig) -> Path:
    config.runs_dir.mkdir(parents=True, exist_ok=True)
    return config.runs_dir


def cycle_to_dict(record: CycleRecord, config: HubConfig | None = None) -> dict:
    metrics = record.metrics
    symbol = config.symbol if config else ""
    timeframe = config.timeframe if config else ""
    return {
        "iteration": record.iteration,
        "params": record.params,
        "accepted": record.accepted,
        "reason": record.reason,
        "score": record.score,
        "pine_snapshot": str(record.pine_snapshot) if record.pine_snapshot else None,
        "symbol": symbol,
        "timeframe": timeframe,
        "metrics": {
            "net_profit_percent": metrics.net_profit_percent,
            "profit_factor": metrics.profit_factor,
            "max_drawdown_percent": metrics.max_drawdown_percent,
            "total_trades": metrics.total_trades,
            "percent_profitable": metrics.percent_profitable,
            "error": metrics.error,
        },
        "analysis": analysis_snapshot(metrics, symbol=symbol, timeframe=timeframe),
        "recorded_at": record.recorded_at,
        "git_commit": record.git_commit,
        "git_dirty": record.git_dirty,
        "hypothesis": record.hypothesis,
        "change": record.change,
        "verdict": record.verdict,
        "lesson": record.lesson,
        "ban": record.ban,
    }


def write_jsonl(path: Path, record: CycleRecord, config: HubConfig | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(cycle_to_dict(record, config), ensure_ascii=True) + "\n")


def _fmt(value: object, digits: int = 2) -> str:
    if value is None:
        return "?"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _key_stats_lines(metrics, config: HubConfig) -> list[str]:
    snap = analysis_snapshot(metrics, symbol=config.symbol, timeframe=config.timeframe)
    currency = snap["currency"] or ""
    wins = snap["winning_trades"]
    trades = snap["total_trades"]
    win_part = f"{_fmt(snap['win_rate_percent'])}%"
    if wins is not None and trades is not None:
        win_part += f"  {wins}/{trades}"
    return [
        "## Key stats",
        "",
        f"- period: {snap['period_start'] or '?'} -> {snap['period_end'] or '?'}"
        f"  ({snap['period_source'] or 'unknown'}, {snap['bar_count'] or '?'} bars)",
        f"- total_pnl: {_fmt(snap['net_profit'])} {currency}  {_fmt(snap['net_profit_percent'])}%"
        "  (cumulative vs initial capital, not annualized)",
        f"- max_drawdown: {_fmt(snap['max_drawdown'])} {currency}  {_fmt(snap['max_drawdown_percent'])}%",
        f"- trades: {trades or '?'}  profitable {win_part}",
        f"- avg_trade: {_fmt(snap['avg_trade'])} {currency}  {_fmt(snap['avg_trade_percent'])}%",
        f"- best_trade: {_fmt(snap['best_trade'])} {currency}  {_fmt(snap['best_trade_percent'])}%",
        f"- worst_trade: {_fmt(snap['worst_trade'])} {currency}  {_fmt(snap['worst_trade_percent'])}%",
        f"- buy_hold: {_fmt(snap['buy_hold_percent'])}%",
        f"- profit_factor: {_fmt(snap['profit_factor'], 3)}",
        "",
        "MDD is equity peak-to-trough, not the worst single trade.",
        "",
    ]


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
            "",
        ]
        lines += _key_stats_lines(best.metrics, config)
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
