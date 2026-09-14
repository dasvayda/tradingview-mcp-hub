from __future__ import annotations

from typing import Any

from hub.models import HubConfig, StrategyMetrics, TargetSpec


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
        net_profit_percent=num("net_profit_percent"),
        profit_factor=num("profit_factor"),
        max_drawdown=num("max_drawdown"),
        max_drawdown_percent=num("max_drawdown_percent"),
        total_trades=integer("total_trades"),
        winning_trades=integer("winning_trades"),
        losing_trades=integer("losing_trades"),
        percent_profitable=num("percent_profitable"),
        avg_trade=num("avg_trade"),
        sharpe_ratio=num("sharpe_ratio"),
        strategy=payload.get("strategy") or inner.get("strategy"),
        currency=payload.get("currency") or inner.get("currency"),
        error=None if inner else (str(error) if error else "empty strategy metrics"),
        raw=payload,
    )


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
