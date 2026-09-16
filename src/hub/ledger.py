from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from hub.metrics import analysis_snapshot, score_metrics
from hub.models import CycleRecord, HubConfig, StrategyMetrics, TargetSpec


VERDICT_KEEP = "keep"
VERDICT_REJECT = "reject"
VERDICT_NOTE = "note"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def short_sha(commit: str | None, dirty: bool = False) -> str:
    if not commit or commit == "unknown":
        text = "unknown"
    else:
        text = commit[:7]
    if dirty:
        text += " dirty"
    return text


def git_state(root: Path) -> tuple[str, bool]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return commit, bool(status.strip())
    except (OSError, subprocess.CalledProcessError):
        return "unknown", True


def _num(value: Any) -> float:
    return float(f"{float(value):.6g}")


def params_match_ban(params: Mapping[str, float], match: Mapping[str, Any] | None) -> bool:
    if not match:
        return False
    for key, expected in match.items():
        if key not in params:
            return False
        try:
            if _num(params[key]) != _num(expected):
                return False
        except (TypeError, ValueError):
            if str(params[key]) != str(expected):
                return False
    return True


def params_diff(previous: Mapping[str, float] | None, current: Mapping[str, float]) -> dict[str, float]:
    if not previous:
        return dict(current)
    changed: dict[str, float] = {}
    for key, value in current.items():
        prior = previous.get(key)
        if prior is None or _num(prior) != _num(value):
            changed[key] = float(value)
    return changed


def describe_change(previous: Mapping[str, float] | None, current: Mapping[str, float]) -> str:
    if not previous:
        return "baseline params"
    parts = []
    for key in sorted(current):
        prior = previous.get(key)
        if prior is None or _num(prior) != _num(current[key]):
            parts.append(f"{key} {prior} -> {current[key]}")
    return "; ".join(parts) if parts else "no param change"


def _same_headline(left: StrategyMetrics, right: StrategyMetrics) -> bool:
    def pack(metrics: StrategyMetrics) -> tuple:
        return (
            round(metrics.net_profit_percent or 0.0, 4),
            round(metrics.profit_factor or 0.0, 4),
            round(metrics.max_drawdown_percent or 0.0, 4),
            metrics.total_trades,
        )

    return pack(left) == pack(right)


def infer_verdict(
    record: CycleRecord,
    previous_best: CycleRecord | None,
    target: TargetSpec,
    previous_params: Mapping[str, float] | None,
) -> tuple[str, dict[str, Any] | None, str]:
    metrics = record.metrics
    if not metrics.ok:
        return VERDICT_NOTE, None, metrics.error or "no metrics"

    dd = metrics.max_drawdown_percent or 0.0
    changed = params_diff(previous_params, record.params) if previous_params else {}
    same_params = bool(previous_params) and not changed

    if dd > target.max_drawdown_percent:
        match = changed if previous_params and changed else None
        ban = {"kind": "params_subset", "match": match} if match else None
        return (
            VERDICT_REJECT,
            ban,
            f"MDD {dd:.2f}% > {target.max_drawdown_percent}% — do not retry this change",
        )

    if same_params:
        return VERDICT_NOTE, None, "retest of the current keep params"

    if previous_best is not None and _same_headline(metrics, previous_best.metrics):
        return VERDICT_NOTE, None, "same tester headline as keep; change did not matter this period"

    prev_np = previous_best.metrics.net_profit_percent if previous_best else None
    cur_np = metrics.net_profit_percent
    if (
        previous_best is not None
        and prev_np is not None
        and cur_np is not None
        and cur_np < prev_np - 1.0
    ):
        ban = {"kind": "params_subset", "match": changed} if changed else None
        return (
            VERDICT_REJECT,
            ban,
            f"NP {cur_np:.2f}% < keep {prev_np:.2f}% — do not keep a lower return",
        )

    if previous_best is not None:
        prev_score = score_metrics(previous_best.metrics, target)
        if record.score < prev_score - 1.0:
            ban = {"kind": "params_subset", "match": changed} if changed else None
            return (
                VERDICT_REJECT,
                ban,
                f"score {record.score:.2f} < best {prev_score:.2f} — worse than keep",
            )

    return VERDICT_KEEP, None, "best so far or first valid cycle"


def load_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entries.append(json.loads(line))
    return entries


def load_banned_matches(path: Path) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for entry in load_entries(path):
        if entry.get("verdict") != VERDICT_REJECT:
            continue
        ban = entry.get("ban") or {}
        match = ban.get("match")
        if isinstance(match, dict) and match:
            matches.append(match)
    return matches


def _np_value(item: dict[str, Any]) -> float:
    metrics = item.get("metrics") or {}
    value = metrics.get("net_profit_percent")
    return float(value) if value is not None else float("-inf")


def _symbol(item: dict[str, Any]) -> str:
    return str(item.get("symbol") or "?")


def best_keep(entries: list[dict[str, Any]], symbol: str | None = None) -> dict[str, Any] | None:
    keeps = [item for item in entries if item.get("verdict") == VERDICT_KEEP]
    if symbol:
        keeps = [item for item in keeps if _symbol(item) == symbol]
    if not keeps:
        return None
    return max(keeps, key=_np_value)


def keeps_by_symbol(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in entries:
        if item.get("verdict") != VERDICT_KEEP:
            continue
        key = _symbol(item)
        current = grouped.get(key)
        if current is None or _np_value(item) > _np_value(current):
            grouped[key] = item
    return grouped


def cycle_from_keep_entry(entry: dict[str, Any]) -> CycleRecord:
    metrics_raw = entry.get("metrics") or {}
    params_raw = entry.get("params") or {}
    metrics = StrategyMetrics(
        net_profit_percent=metrics_raw.get("net_profit_percent"),
        profit_factor=metrics_raw.get("profit_factor"),
        max_drawdown_percent=metrics_raw.get("max_drawdown_percent"),
        total_trades=metrics_raw.get("total_trades"),
        percent_profitable=metrics_raw.get("win_rate_percent"),
        period_start=metrics_raw.get("period_start"),
        period_end=metrics_raw.get("period_end"),
        strategy=entry.get("strategy"),
    )
    params = {str(key): float(value) for key, value in params_raw.items()}
    return CycleRecord(
        iteration=0,
        params=params,
        metrics=metrics,
        score=float(entry.get("score") or 0.0),
        accepted=False,
        reason=str(entry.get("reason") or ""),
        verdict=VERDICT_KEEP,
        change=str(entry.get("change") or ""),
        lesson=str(entry.get("lesson") or ""),
    )


def load_ledger_best(path: Path, symbol: str | None = None) -> CycleRecord | None:
    keep = best_keep(load_entries(path), symbol=symbol)
    if keep is None:
        return None
    return cycle_from_keep_entry(keep)


def _fmt(value: object, digits: int = 2) -> str:
    if value is None:
        return "?"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_markdown(entries: list[dict[str, Any]]) -> str:
    grouped = keeps_by_symbol(entries)
    lines = [
        "# Backtest ledger",
        "",
        "파인이나 파라미터를 바꾸기 **전에** 이 파일과 `ledger.jsonl` 을 읽음.",
        "`verdict: reject` 의 `ban.match` 와 같은 변경은 새 근거 없이 다시 하지 않음.",
        "Keep 비교는 **같은 종목** 끼리만 함. 런타임 `runs/` 로그는 git에 안 남음.",
        "",
        "## Keep (종목별 베스트)",
        "",
    ]
    if grouped:
        for symbol in sorted(grouped):
            keep = grouped[symbol]
            metrics = keep.get("metrics") or {}
            lines += [
                f"### `{symbol}`",
                "",
                f"- id: `{keep.get('id')}`",
                f"- date: {keep.get('recorded_at')}",
                f"- commit: `{short_sha(keep.get('git_commit'), bool(keep.get('git_dirty')))}`",
                f"- strategy: {keep.get('strategy') or '?'}",
                f"- change: {keep.get('change') or keep.get('hypothesis') or '?'}",
                (
                    f"- result: NP {_fmt(metrics.get('net_profit_percent'))}%  "
                    f"PF {_fmt(metrics.get('profit_factor'), 3)}  "
                    f"MDD {_fmt(metrics.get('max_drawdown_percent'))}%  "
                    f"trades {metrics.get('total_trades') or '?'}"
                ),
                f"- lesson: {keep.get('lesson') or '-'}",
                "",
            ]
    else:
        lines += ["아직 keep 기록이 없음.", ""]

    lines += [
        "## Do not retry",
        "",
        "| date | symbol | commit | change | why | ban.match |",
        "|------|--------|--------|--------|-----|-----------|",
    ]
    rejects = [item for item in entries if item.get("verdict") == VERDICT_REJECT]
    if not rejects:
        lines.append("| - | - | - | - | - | - |")
    for item in rejects:
        ban = item.get("ban") or {}
        match = ban.get("match") or ban.get("tag") or ""
        if isinstance(match, dict):
            match = json.dumps(match, ensure_ascii=True, sort_keys=True)
        lines.append(
            "| {date} | `{symbol}` | `{commit}` | {change} | {why} | `{match}` |".format(
                date=(item.get("recorded_at") or "?")[:10],
                symbol=_symbol(item),
                commit=short_sha(item.get("git_commit"), bool(item.get("git_dirty"))),
                change=(item.get("change") or item.get("hypothesis") or "?").replace("|", "/"),
                why=(item.get("lesson") or item.get("reason") or "").replace("|", "/"),
                match=match or ban.get("kind") or "",
            )
        )

    lines += [
        "",
        "## Chronology",
        "",
        "| date | symbol | commit | change | NP% | PF | MDD% | trades | verdict |",
        "|------|--------|--------|--------|-----|----|------|--------|---------|",
    ]
    if not entries:
        lines.append("| - | - | - | - | - | - | - | - | - |")
    for item in entries:
        metrics = item.get("metrics") or {}
        lines.append(
            "| {date} | `{symbol}` | `{commit}` | {change} | {np} | {pf} | {mdd} | {trades} | {verdict} |".format(
                date=(item.get("recorded_at") or "?")[:10],
                symbol=_symbol(item),
                commit=short_sha(item.get("git_commit"), bool(item.get("git_dirty"))),
                change=(item.get("change") or item.get("hypothesis") or "?").replace("|", "/"),
                np=_fmt(metrics.get("net_profit_percent")),
                pf=_fmt(metrics.get("profit_factor"), 3),
                mdd=_fmt(metrics.get("max_drawdown_percent")),
                trades=metrics.get("total_trades") if metrics.get("total_trades") is not None else "?",
                verdict=item.get("verdict") or "note",
            )
        )
    lines.append("")
    return "\n".join(lines)


def rewrite_markdown(jsonl_path: Path, markdown_path: Path) -> None:
    markdown_path.write_text(render_markdown(load_entries(jsonl_path)), encoding="utf-8")


def append_entry(jsonl_path: Path, markdown_path: Path, entry: dict[str, Any]) -> dict[str, Any]:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(entry)
    payload.setdefault("recorded_at", utc_now())
    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
    rewrite_markdown(jsonl_path, markdown_path)
    return payload


def cycle_to_ledger_entry(
    record: CycleRecord,
    config: HubConfig,
    *,
    previous_params: Mapping[str, float] | None = None,
    previous_best: CycleRecord | None = None,
) -> dict[str, Any]:
    metrics = record.metrics
    recorded_at = record.recorded_at or utc_now()
    git_commit = record.git_commit
    git_dirty = record.git_dirty
    if git_commit is None:
        git_commit, git_dirty = git_state(config.root)
    change = record.change
    if not change:
        if previous_params:
            change = describe_change(previous_params, record.params)
        else:
            change = f"first test on {config.symbol}"
    hypothesis = record.hypothesis or change
    verdict = record.verdict
    ban = record.ban
    lesson = record.lesson
    if not verdict:
        verdict, ban, lesson = infer_verdict(record, previous_best, config.target, previous_params)
    elif not lesson:
        _, _, lesson = infer_verdict(record, previous_best, config.target, previous_params)
    snapshot = analysis_snapshot(metrics, symbol=config.symbol, timeframe=config.timeframe)
    entry_id = recorded_at.replace(":", "").replace("-", "")
    return {
        "id": entry_id,
        "recorded_at": recorded_at,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "symbol": config.symbol,
        "timeframe": config.timeframe,
        "strategy": metrics.strategy,
        "hypothesis": hypothesis,
        "change": change,
        "params": dict(record.params),
        "verdict": verdict,
        "reason": record.reason,
        "lesson": lesson,
        "score": record.score,
        "ban": ban,
        "pine_snapshot": str(record.pine_snapshot) if record.pine_snapshot else None,
        "report": str(record.report_path) if record.report_path else None,
        "metrics": {
            "net_profit_percent": snapshot["net_profit_percent"],
            "profit_factor": snapshot["profit_factor"],
            "max_drawdown_percent": snapshot["max_drawdown_percent"],
            "total_trades": snapshot["total_trades"],
            "win_rate_percent": snapshot["win_rate_percent"],
            "period_start": snapshot["period_start"],
            "period_end": snapshot["period_end"],
        },
    }


def append_cycle(
    record: CycleRecord,
    config: HubConfig,
    *,
    previous_params: Mapping[str, float] | None = None,
    previous_best: CycleRecord | None = None,
) -> dict[str, Any]:
    entry = cycle_to_ledger_entry(
        record,
        config,
        previous_params=previous_params,
        previous_best=previous_best,
    )
    record.recorded_at = entry["recorded_at"]
    record.git_commit = entry["git_commit"]
    record.git_dirty = bool(entry["git_dirty"])
    record.hypothesis = entry["hypothesis"]
    record.change = entry["change"]
    record.verdict = entry["verdict"]
    record.lesson = entry["lesson"]
    record.ban = entry.get("ban")
    return append_entry(config.ledger_jsonl, config.ledger_md, entry)


def metrics_from_cycle_dict(payload: dict[str, Any]) -> StrategyMetrics:
    raw_metrics = payload.get("metrics") or {}
    analysis = payload.get("analysis") or {}
    merged = {**raw_metrics, **{k: v for k, v in analysis.items() if v is not None}}
    return StrategyMetrics(
        net_profit=merged.get("net_profit"),
        net_profit_percent=merged.get("net_profit_percent"),
        profit_factor=merged.get("profit_factor"),
        max_drawdown=merged.get("max_drawdown"),
        max_drawdown_percent=merged.get("max_drawdown_percent"),
        total_trades=merged.get("total_trades"),
        winning_trades=merged.get("winning_trades"),
        losing_trades=merged.get("losing_trades"),
        percent_profitable=merged.get("percent_profitable") or merged.get("win_rate_percent"),
        avg_trade=merged.get("avg_trade"),
        avg_trade_percent=merged.get("avg_trade_percent"),
        largest_win=merged.get("best_trade"),
        largest_win_percent=merged.get("best_trade_percent"),
        largest_loss=merged.get("worst_trade"),
        largest_loss_percent=merged.get("worst_trade_percent"),
        buy_hold_percent=merged.get("buy_hold_percent"),
        commission_paid=merged.get("commission_paid"),
        period_start=merged.get("period_start"),
        period_end=merged.get("period_end"),
        period_source=merged.get("period_source"),
        bar_count=merged.get("bar_count"),
        strategy=analysis.get("strategy") or merged.get("strategy"),
        currency=merged.get("currency"),
        error=raw_metrics.get("error"),
    )


def record_from_cycle_file(
    path: Path,
    config: HubConfig,
    *,
    hypothesis: str = "",
    change: str = "",
    verdict: str = "",
    lesson: str = "",
    ban_match: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"no cycles in {path}")
    payload = json.loads(lines[-1])
    metrics = metrics_from_cycle_dict(payload)
    params = {str(k): float(v) for k, v in (payload.get("params") or {}).items()}
    if not metrics.ok:
        score = -1000.0
    else:
        score = score_metrics(metrics, config.target)
    record = CycleRecord(
        iteration=int(payload.get("iteration") or 0),
        params=params,
        metrics=metrics,
        score=float(payload.get("score") or score),
        accepted=bool(payload.get("accepted")),
        reason=str(payload.get("reason") or ""),
        pine_snapshot=Path(payload["pine_snapshot"]) if payload.get("pine_snapshot") else None,
        hypothesis=hypothesis,
        change=change,
        verdict=verdict,
        lesson=lesson,
        ban={"kind": "params_subset", "match": ban_match} if ban_match else None,
    )
    previous_best = None
    keep = best_keep(load_entries(config.ledger_jsonl), symbol=config.symbol)
    if keep and keep.get("params"):
        keep_metrics = StrategyMetrics(
            net_profit_percent=(keep.get("metrics") or {}).get("net_profit_percent"),
            profit_factor=(keep.get("metrics") or {}).get("profit_factor"),
            max_drawdown_percent=(keep.get("metrics") or {}).get("max_drawdown_percent"),
            total_trades=(keep.get("metrics") or {}).get("total_trades"),
            strategy=keep.get("strategy"),
        )
        previous_best = CycleRecord(
            iteration=0,
            params={str(k): float(v) for k, v in keep["params"].items()},
            metrics=keep_metrics,
            score=float(keep.get("score") or 0.0),
            accepted=False,
            reason="",
            verdict=VERDICT_KEEP,
        )
    previous_params = previous_best.params if previous_best else None
    return append_cycle(record, config, previous_params=previous_params, previous_best=previous_best)
