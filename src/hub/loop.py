from __future__ import annotations

from pathlib import Path
import time
from typing import Callable

from hub import pine
from hub.ledger import append_cycle, git_state, load_banned_matches, load_ledger_best, utc_now
from hub.metrics import evaluate
from hub.models import CycleRecord, HubConfig, LoopResult, StrategyMetrics
from hub.mutate import ParamSearch
from hub.report import ensure_runs_dir, write_jsonl, write_markdown
from hub.tv_client import DryRunTvClient, TvClient, TvCliClient, TvCliError


def _fatal_pine_errors(payload: dict) -> list:
    raw = payload.get("errors") or payload.get("items") or []
    if not isinstance(raw, list):
        return [raw] if raw else []
    fatal = []
    for item in raw:
        if isinstance(item, dict) and int(item.get("severity") or 0) >= 4:
            fatal.append(item)
        elif isinstance(item, str) and item.strip():
            fatal.append(item)
    return fatal


def _copy_best_pine(current: Path, dest: Path) -> None:
    dest.write_text(current.read_text(encoding="utf-8"), encoding="utf-8")


class BacktestLoop:
    def __init__(self, config: HubConfig, client: TvClient, dry_run: bool = False) -> None:
        self.config = config
        self.client = client
        self.dry_run = dry_run
        self.template = pine.read_source(config.pine.source_path)
        self.params = pine.extract_params(self.template)
        self.search = ParamSearch(
            config.mutation.knobs,
            config.mutation.seed,
            banned_matches=load_banned_matches(config.ledger_jsonl),
        )
        self.removed_strategies: list[str] = []

    def _prepare_chart(self) -> None:
        self.client.health()
        if self.config.layout:
            self.client.switch_layout(self.config.layout)
            time.sleep(max(3.0, self.config.tv.compile_wait_seconds))
        self.client.set_symbol(self.config.symbol)
        self.client.set_timeframe(self.config.timeframe)
        self.client.ensure_strategy_editor()
        self.removed_strategies = self.client.remove_foreign_strategies()
        self.client.new_strategy()

    def _write_iteration_pine(self, iteration: int) -> Path:
        runs = ensure_runs_dir(self.config)
        snapshot = runs / f"iter-{iteration:03d}.pine"
        pine.snapshot_with_params(self.template, self.params, self.config.pine.current_path)
        pine.snapshot_with_params(self.template, self.params, snapshot)
        return snapshot

    def _backtest(self, snapshot: Path) -> CycleRecord:
        self.client.set_pine(self.config.pine.current_path)
        self.client.compile_pine()
        errors: list = []
        try:
            error_payload = self.client.pine_errors()
            errors = _fatal_pine_errors(error_payload)
        except TvCliError:
            errors = []
        if errors:
            metrics = StrategyMetrics(error=f"pine compile errors: {errors}")
            _, score, reason = evaluate(metrics, self.config)
            return CycleRecord(
                iteration=0,
                params=dict(self.params),
                metrics=metrics,
                score=score,
                accepted=False,
                reason=reason,
                pine_snapshot=snapshot,
            )
        metrics = self.client.wait_for_results()
        expected = "HUB DOGE"
        if metrics.ok and metrics.strategy and expected not in str(metrics.strategy):
            metrics = StrategyMetrics(
                error=(
                    f"tester is reading '{metrics.strategy}', not the hub script. "
                    "Close/remove other strategies on the chart (eye-hide is not enough), "
                    "then Pine Editor: Open > New > Strategy so Save does not overwrite an existing file."
                ),
                strategy=metrics.strategy,
                raw=metrics.raw,
            )
        hit, score, reason = evaluate(metrics, self.config)
        return CycleRecord(
            iteration=0,
            params=dict(self.params),
            metrics=metrics,
            score=score,
            accepted=hit,
            reason=reason,
            pine_snapshot=snapshot,
        )

    def run(self, progress: Callable[[str], None] | None = None) -> LoopResult:
        log = progress or (lambda _msg: None)
        history: list[CycleRecord] = []
        jsonl = ensure_runs_dir(self.config) / "cycles.jsonl"
        self._prepare_chart()
        if self.removed_strategies:
            log("closed chart strategies: " + ", ".join(self.removed_strategies))
        self.search.mark(self.params)

        best: CycleRecord | None = None
        ledger_best = load_ledger_best(self.config.ledger_jsonl, symbol=self.config.symbol)
        status = "loop_limit"

        cycles = 1 if self.config.mutation.mode == "agent" else self.config.loop_limit
        for iteration in range(1, cycles + 1):
            snapshot = self._write_iteration_pine(iteration)
            record = self._backtest(snapshot)
            record.iteration = iteration
            record.recorded_at = utc_now()
            record.git_commit, record.git_dirty = git_state(self.config.root)
            previous_params = history[-1].params if history else (ledger_best.params if ledger_best else None)
            previous_best = best
            if ledger_best is not None and (previous_best is None or ledger_best.score > previous_best.score):
                previous_best = ledger_best
            append_cycle(
                record,
                self.config,
                previous_params=previous_params,
                previous_best=previous_best,
            )
            history.append(record)
            write_jsonl(jsonl, record, self.config)
            log(
                f"iter {iteration}/{cycles} score={record.score:.2f} "
                f"np%={record.metrics.net_profit_percent} "
                f"verdict={record.verdict or '-'} reason={record.reason}"
            )

            if record.verdict != "reject" and (best is None or record.score > best.score):
                best = record
                _copy_best_pine(self.config.pine.current_path, self.config.runs_dir / "best.pine")

            hit, _, _ = evaluate(record.metrics, self.config)
            if hit:
                status = "target_hit"
                break

            if self.config.mutation.mode == "agent":
                status = "awaiting_agent_edit"
                break

            keep_params = self.params
            if best is not None:
                keep_params = best.params
            elif ledger_best is not None:
                keep_params = ledger_best.params
            nxt = self.search.next_candidate(keep_params)
            if nxt is None:
                status = "search_exhausted"
                break
            self.params = nxt

        result = LoopResult(
            status=status,
            iterations=len(history),
            best=best,
            history=history,
        )
        result.report_path = write_markdown(result, self.config)
        return result


def build_client(config: HubConfig, dry_run: bool) -> tuple[TvClient, BacktestLoop]:
    loop_holder: dict[str, BacktestLoop] = {}

    def current_params():
        return loop_holder["loop"].params

    client: TvClient
    if dry_run:
        client = DryRunTvClient(config, current_params)
    else:
        client = TvCliClient(config)
    loop = BacktestLoop(config, client, dry_run=dry_run)
    loop_holder["loop"] = loop
    return client, loop
