from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from hub.models import HubConfig, StrategyMetrics, TargetSpec

# TradingView internal_api stores many "percent" fields as ratios (0.09 = 9%).
# Values already in percent-points (21.4, -9.0) have abs > this cutoff.
_RATIO_ABS_MAX = 2.0


def as_percent(value: float | None) -> float | None:
    if value is None:
        return None
    if abs(value) <= _RATIO_ABS_MAX:
        return value * 100.0
    return value


def metrics_from_payload(payload: dict[str, Any]) -> StrategyMetrics:
    inner = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else payload
    error = payload.get("error")
    if not inner and error:
        return StrategyMetrics(error=str(error), raw=payload)

    def num(key: str) -> float | None:
        value = inner.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def integer(key: str) -> int | None:
        value = num(key)
        return None if value is None else int(round(value))

    return StrategyMetrics(
        net_profit=num("net_profit"),
        net_profit_percent=as_percent(num("net_profit_percent")),
        profit_factor=num("profit_factor"),
        max_drawdown=num("max_drawdown"),
        max_drawdown_percent=as_percent(num("max_drawdown_percent")),
        total_trades=integer("total_trades"),
        winning_trades=integer("winning_trades"),
        losing_trades=integer("losing_trades"),
        percent_profitable=as_percent(num("percent_profitable")),
        avg_trade=num("avg_trade"),
        avg_trade_percent=as_percent(num("avg_trade_percent")),
        sharpe_ratio=num("sharpe_ratio"),
        largest_win=num("largest_win"),
        largest_win_percent=as_percent(num("largest_win_percent")),
        largest_loss=num("largest_loss"),
        largest_loss_percent=as_percent(num("largest_loss_percent")),
        buy_hold_return=num("buy_hold_return"),
        buy_hold_percent=as_percent(num("buy_hold_percent") if inner.get("buy_hold_percent") is not None else num("buy_hold_return_percent")),
        commission_paid=num("commission_paid"),
        period_start=(
            str(inner["period_start"])
            if inner.get("period_start")
            else unix_to_iso(num("period_from_unix"))
        ),
        period_end=(
            str(inner["period_end"])
            if inner.get("period_end")
            else unix_to_iso(num("period_to_unix"))
        ),
        period_source=str(inner["period_source"]) if inner.get("period_source") else None,
        bar_count=integer("bar_count"),
        strategy=payload.get("strategy") or inner.get("strategy"),
        currency=payload.get("currency") or inner.get("currency"),
        error=None if inner else (str(error) if error else "empty strategy metrics"),
        raw=payload,
    )


def unix_to_iso(value: float | int | None) -> str | None:
    if value is None:
        return None
    seconds = float(value)
    if seconds > 1e12:
        seconds = seconds / 1000.0
    if seconds <= 0:
        return None
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def merge_analysis(metrics: StrategyMetrics, extra: dict[str, Any]) -> StrategyMetrics:
    """Fill period / extra tester fields without dropping the headline stats."""
    if not extra:
        return metrics
    updates: dict[str, Any] = {}
    for key in (
        "avg_trade_percent",
        "largest_win",
        "largest_win_percent",
        "largest_loss",
        "largest_loss_percent",
        "buy_hold_percent",
        "commission_paid",
        "period_start",
        "period_end",
        "period_source",
        "bar_count",
    ):
        incoming = extra.get(key)
        if incoming is None:
            continue
        current = getattr(metrics, key)
        if current is None:
            updates[key] = incoming
    return replace(metrics, **updates) if updates else metrics


def analysis_snapshot(metrics: StrategyMetrics, *, symbol: str, timeframe: str) -> dict[str, Any]:
    """Canonical backtest card. Net profit % is cumulative vs initial capital, not annualized."""
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy": metrics.strategy,
        "currency": metrics.currency,
        "period_start": metrics.period_start,
        "period_end": metrics.period_end,
        "period_source": metrics.period_source,
        "bar_count": metrics.bar_count,
        "total_trades": metrics.total_trades,
        "winning_trades": metrics.winning_trades,
        "losing_trades": metrics.losing_trades,
        "win_rate_percent": metrics.percent_profitable,
        "net_profit": metrics.net_profit,
        "net_profit_percent": metrics.net_profit_percent,
        "avg_trade": metrics.avg_trade,
        "avg_trade_percent": metrics.avg_trade_percent,
        "best_trade": metrics.largest_win,
        "best_trade_percent": metrics.largest_win_percent,
        "worst_trade": metrics.largest_loss,
        "worst_trade_percent": metrics.largest_loss_percent,
        "max_drawdown": metrics.max_drawdown,
        "max_drawdown_percent": metrics.max_drawdown_percent,
        "profit_factor": metrics.profit_factor,
        "buy_hold_percent": metrics.buy_hold_percent,
        "commission_paid": metrics.commission_paid,
    }


def score_metrics(metrics: StrategyMetrics, target: TargetSpec) -> float:
    if not metrics.ok:
        return -1_000.0
    profit = metrics.net_profit_percent or 0.0
    trades = metrics.total_trades or 0
    pf = metrics.profit_factor or 0.0
    dd = metrics.max_drawdown_percent or 0.0
    trade_bonus = min(trades, target.min_trades) * 0.15
    pf_bonus = max(pf - 1.0, -1.0) * 8.0
    dd_penalty = max(0.0, dd - target.max_drawdown_percent) * 1.5
    return profit + trade_bonus + pf_bonus - dd_penalty


def target_hit(metrics: StrategyMetrics, target: TargetSpec) -> tuple[bool, str]:
    if not metrics.ok:
        return False, metrics.error or "no metrics"
    checks = [
        (
            (metrics.net_profit_percent or -1e9) >= target.net_profit_percent,
            f"net_profit_percent {metrics.net_profit_percent} < {target.net_profit_percent}",
        ),
        (
            (metrics.total_trades or 0) >= target.min_trades,
            f"total_trades {metrics.total_trades} < {target.min_trades}",
        ),
        (
            (metrics.profit_factor or 0) >= target.min_profit_factor,
            f"profit_factor {metrics.profit_factor} < {target.min_profit_factor}",
        ),
        (
            (metrics.max_drawdown_percent or 0) <= target.max_drawdown_percent,
            f"max_drawdown_percent {metrics.max_drawdown_percent} > {target.max_drawdown_percent}",
        ),
    ]
    failed = [reason for ok, reason in checks if not ok]
    if failed:
        return False, "; ".join(failed)
    return True, "all targets met"


def evaluate(metrics: StrategyMetrics, config: HubConfig) -> tuple[bool, float, str]:
    hit, reason = target_hit(metrics, config.target)
    return hit, score_metrics(metrics, config.target), reason
