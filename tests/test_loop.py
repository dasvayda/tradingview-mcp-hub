from pathlib import Path

import yaml

from hub.config import load_config
from hub.loop import build_client


def test_dry_run_loop_moves_toward_target(tmp_path: Path):
    base = load_config()
    payload = {
        "symbol": base.symbol,
        "timeframe": base.timeframe,
        "layout": "HUB-DOGE-BT",
        "loop_limit": 12,
        "initial_capital": base.initial_capital,
        "target": {
            "net_profit_percent": 20.0,
            "min_trades": 20,
            "min_profit_factor": 1.2,
            "max_drawdown_percent": 35.0,
        },
        "pine": {
            "source_path": str(base.pine.source_path),
            "current_path": str(tmp_path / "current.pine"),
        },
        "tv": {"command": ["tv"]},
        "mutation": {
            "mode": "params",
            "seed": 7,
            "knobs": {
                "ma_len": [34, 50, 89],
                "atr_mult": [1.5, 2.0, 2.5],
                "rr_ratio": [1.5, 2.0, 2.5],
                "reclaim_pct": [1.005, 1.015, 1.03],
            },
        },
        "output": {"runs_dir": str(tmp_path / "runs")},
        "ledger": {
            "jsonl": str(tmp_path / "ledger.jsonl"),
            "markdown": str(tmp_path / "ledger.md"),
        },
    }
    config_path = tmp_path / "cfg.yaml"
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    config = load_config(config_path)
    _, loop = build_client(config, dry_run=True)
    result = loop.run()
    assert result.iterations >= 1
    assert result.best is not None
    assert result.status in {"target_hit", "loop_limit", "search_exhausted"}
    assert result.best.score > -1000
    if result.status == "target_hit":
        assert result.best.metrics.net_profit_percent >= 20.0
    assert (tmp_path / "ledger.jsonl").exists()
    assert "Keep" in (tmp_path / "ledger.md").read_text(encoding="utf-8")


def test_agent_mode_runs_one_cycle(tmp_path: Path):
    base = load_config()
    payload = {
        "symbol": base.symbol,
        "timeframe": "60",
        "loop_limit": 20,
        "initial_capital": 10000,
        "target": {
            "net_profit_percent": 99.0,
            "min_trades": 20,
            "min_profit_factor": 1.2,
            "max_drawdown_percent": 35.0,
        },
        "pine": {
            "source_path": str(base.pine.source_path),
            "current_path": str(tmp_path / "current.pine"),
        },
        "mutation": {"mode": "agent", "seed": 1, "knobs": {"ma_len": [34, 50]}},
        "output": {"runs_dir": str(tmp_path / "runs")},
        "ledger": {
            "jsonl": str(tmp_path / "ledger.jsonl"),
            "markdown": str(tmp_path / "ledger.md"),
        },
    }
    config_path = tmp_path / "agent.yaml"
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    _, loop = build_client(load_config(config_path), dry_run=True)
    result = loop.run()
    assert result.iterations == 1
    assert result.status == "awaiting_agent_edit"
    assert result.history[0].verdict in {"keep", "reject", "note"}
    assert (tmp_path / "ledger.jsonl").exists()
