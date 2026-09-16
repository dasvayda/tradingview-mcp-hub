import json
from pathlib import Path

from hub.ledger import (
    append_entry,
    best_keep,
    infer_verdict,
    load_banned_matches,
    params_match_ban,
    render_markdown,
    rewrite_markdown,
)
from hub.models import CycleRecord, StrategyMetrics, TargetSpec


def _target() -> TargetSpec:
    return TargetSpec(
        net_profit_percent=20.0,
        min_trades=20,
        min_profit_factor=1.2,
        max_drawdown_percent=35.0,
    )


def test_params_match_ban_is_subset():
    params = {"reclaim_pct": 1.005, "atr_mult": 2.0, "cooldown_days": 2.0}
    assert params_match_ban(params, {"reclaim_pct": 1.005})
    assert not params_match_ban(params, {"reclaim_pct": 1.015})
    assert not params_match_ban(params, {"reclaim_pct": 1.005, "cooldown_days": 1.0})


def test_mdd_blow_is_reject_with_ban():
    previous = CycleRecord(
        iteration=1,
        params={"reclaim_pct": 1.015, "atr_mult": 2.0},
        metrics=StrategyMetrics(net_profit_percent=66.4, profit_factor=2.4, max_drawdown_percent=27.0, total_trades=7),
        score=78.0,
        accepted=False,
        reason="ok",
        verdict="keep",
    )
    worse = CycleRecord(
        iteration=2,
        params={"reclaim_pct": 1.005, "atr_mult": 2.0},
        metrics=StrategyMetrics(net_profit_percent=63.3, profit_factor=1.7, max_drawdown_percent=37.8, total_trades=13),
        score=66.0,
        accepted=False,
        reason="mdd",
    )
    verdict, ban, lesson = infer_verdict(worse, previous, _target(), previous.params)
    assert verdict == "reject"
    assert ban == {"kind": "params_subset", "match": {"reclaim_pct": 1.005}}
    assert "MDD" in lesson


def test_same_params_retest_is_note():
    keep = CycleRecord(
        iteration=1,
        params={"reclaim_pct": 1.015, "atr_mult": 2.0},
        metrics=StrategyMetrics(net_profit_percent=66.4, profit_factor=2.4, max_drawdown_percent=27.0, total_trades=7),
        score=78.0,
        accepted=False,
        reason="ok",
        verdict="keep",
    )
    retest = CycleRecord(
        iteration=2,
        params={"reclaim_pct": 1.015, "atr_mult": 2.0},
        metrics=StrategyMetrics(net_profit_percent=66.1, profit_factor=2.39, max_drawdown_percent=27.1, total_trades=7),
        score=77.6,
        accepted=False,
        reason="trades",
    )
    verdict, ban, lesson = infer_verdict(retest, keep, _target(), keep.params)
    assert verdict == "note"
    assert ban is None
    assert "retest" in lesson


def test_identical_headline_is_note_not_reject():
    keep = CycleRecord(
        iteration=1,
        params={"lookback_days": 10.0, "ma_len": 89.0},
        metrics=StrategyMetrics(net_profit_percent=93.3597, profit_factor=9.9684, max_drawdown_percent=14.2698, total_trades=4),
        score=165.0,
        accepted=False,
        reason="ok",
        verdict="keep",
    )
    lookback = CycleRecord(
        iteration=2,
        params={"lookback_days": 14.0, "ma_len": 89.0},
        metrics=StrategyMetrics(net_profit_percent=93.3597, profit_factor=9.9684, max_drawdown_percent=14.2698, total_trades=4),
        score=110.0,
        accepted=False,
        reason="trades",
    )
    verdict, ban, lesson = infer_verdict(lookback, keep, _target(), keep.params)
    assert verdict == "note"
    assert ban is None
    assert "headline" in lesson


def test_lower_np_rejects_even_when_pf_score_is_huge():
    keep = CycleRecord(
        iteration=1,
        params={"reclaim_pct": 1.015, "ma_len": 89.0},
        metrics=StrategyMetrics(net_profit_percent=93.36, profit_factor=9.97, max_drawdown_percent=14.3, total_trades=4),
        score=165.0,
        accepted=False,
        reason="ok",
        verdict="keep",
    )
    two_wins = CycleRecord(
        iteration=2,
        params={"reclaim_pct": 1.03, "ma_len": 89.0},
        metrics=StrategyMetrics(net_profit_percent=59.32, profit_factor=373.0, max_drawdown_percent=14.3, total_trades=2),
        score=3000.0,
        accepted=False,
        reason="trades",
    )
    verdict, ban, lesson = infer_verdict(two_wins, keep, _target(), keep.params)
    assert verdict == "reject"
    assert ban == {"kind": "params_subset", "match": {"reclaim_pct": 1.03}}
    assert "NP" in lesson


def test_append_rebuilds_markdown(tmp_path: Path):
    jsonl = tmp_path / "ledger.jsonl"
    markdown = tmp_path / "ledger.md"
    append_entry(
        jsonl,
        markdown,
        {
            "id": "keep-1",
            "recorded_at": "2026-09-16T17:16:55Z",
            "git_commit": "c5be91a1af7e0ec6e18ea80bee50b9a51e55a44f",
            "git_dirty": True,
            "change": "daily MA reclaim baseline",
            "verdict": "keep",
            "symbol": "BINANCE:DOGEUSDT",
            "lesson": "keep this as base",
            "metrics": {
                "net_profit_percent": 66.43,
                "profit_factor": 2.415,
                "max_drawdown_percent": 26.97,
                "total_trades": 7,
            },
        },
    )
    append_entry(
        jsonl,
        markdown,
        {
            "id": "reject-1",
            "recorded_at": "2026-09-16T17:17:52Z",
            "git_commit": "c5be91a1af7e0ec6e18ea80bee50b9a51e55a44f",
            "git_dirty": True,
            "change": "reclaim_pct 1.015 -> 1.005",
            "verdict": "reject",
            "symbol": "BINANCE:DOGEUSDT",
            "lesson": "MDD blew past 35",
            "ban": {"kind": "params_subset", "match": {"reclaim_pct": 1.005}},
            "metrics": {
                "net_profit_percent": 63.29,
                "profit_factor": 1.702,
                "max_drawdown_percent": 37.81,
                "total_trades": 13,
            },
        },
    )
    text = markdown.read_text(encoding="utf-8")
    assert "66.43" in text
    assert "`BINANCE:DOGEUSDT`" in text
    assert "Do not retry" in text
    assert "reclaim_pct" in text
    rewrite_markdown(jsonl, markdown)
    bans = load_banned_matches(jsonl)
    assert bans == [{"reclaim_pct": 1.005}]
    rows = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines()]
    rendered = render_markdown(rows)
    assert "c5be91a dirty" in rendered


def test_best_keep_is_per_symbol():
    entries = [
        {
            "symbol": "BINANCE:DOGEUSDT",
            "verdict": "keep",
            "metrics": {"net_profit_percent": 93.0},
        },
        {
            "symbol": "BINANCE:ZECUSDT",
            "verdict": "keep",
            "metrics": {"net_profit_percent": 12.0},
        },
    ]
    doge = best_keep(entries, symbol="BINANCE:DOGEUSDT")
    zec = best_keep(entries, symbol="BINANCE:ZECUSDT")
    assert doge is not None and doge["metrics"]["net_profit_percent"] == 93.0
    assert zec is not None and zec["metrics"]["net_profit_percent"] == 12.0
    text = render_markdown(entries)
    assert "### `BINANCE:DOGEUSDT`" in text
    assert "### `BINANCE:ZECUSDT`" in text
