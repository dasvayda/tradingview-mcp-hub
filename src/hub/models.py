from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TargetSpec:
    net_profit_percent: float
    min_trades: int
    min_profit_factor: float
    max_drawdown_percent: float


@dataclass(frozen=True)
class PineSpec:
    source_path: Path
    current_path: Path


@dataclass(frozen=True)
class TvSpec:
    command: tuple[str, ...]
    cdp_port: int
    compile_wait_seconds: float
    results_wait_seconds: float
    results_retries: int
    screenshot: bool
    clear_existing_strategies: bool
    keep_strategy_substring: str


@dataclass(frozen=True)
class MutationSpec:
    mode: str
    seed: int
    knobs: dict[str, tuple[float, ...]]


@dataclass(frozen=True)
class HubConfig:
    symbol: str
    timeframe: str
    layout: str | None
    loop_limit: int
    initial_capital: float
    target: TargetSpec
    pine: PineSpec
    tv: TvSpec
    mutation: MutationSpec
    runs_dir: Path
    root: Path
    raw: dict[str, Any] = field(repr=False, default_factory=dict)


@dataclass(frozen=True)
class StrategyMetrics:
    net_profit: float | None = None
    net_profit_percent: float | None = None
    profit_factor: float | None = None
    max_drawdown: float | None = None
    max_drawdown_percent: float | None = None
    total_trades: int | None = None
    winning_trades: int | None = None
    losing_trades: int | None = None
    percent_profitable: float | None = None
    avg_trade: float | None = None
    avg_trade_percent: float | None = None
    largest_win: float | None = None
    largest_win_percent: float | None = None
    largest_loss: float | None = None
    largest_loss_percent: float | None = None
    buy_hold_return: float | None = None
    buy_hold_percent: float | None = None
    commission_paid: float | None = None
    sharpe_ratio: float | None = None
    period_start: str | None = None
    period_end: str | None = None
    period_source: str | None = None
    bar_count: int | None = None
    strategy: str | None = None
    currency: str | None = None
    error: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def ok(self) -> bool:
        return self.error is None and self.net_profit_percent is not None


@dataclass
class CycleRecord:
    iteration: int
    params: dict[str, float]
    metrics: StrategyMetrics
    score: float
    accepted: bool
    reason: str
    pine_snapshot: Path | None = None


@dataclass
class LoopResult:
    status: str
    iterations: int
    best: CycleRecord | None
    history: list[CycleRecord]
    report_path: Path | None = None
