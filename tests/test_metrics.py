from hub.metrics import analysis_snapshot, metrics_from_payload, score_metrics, target_hit, unix_to_iso
from hub.models import TargetSpec


def _target() -> TargetSpec:
    return TargetSpec(
        net_profit_percent=20.0,
        min_trades=20,
        min_profit_factor=1.2,
        max_drawdown_percent=35.0,
    )


def test_parse_strategy_tester_payload():
    payload = {
        "success": True,
        "strategy": "HUB DOGE EMA RSI ATR",
        "currency": "USD",
        "metrics": {
            "net_profit_percent": 21.4,
            "profit_factor": 1.6,
            "max_drawdown_percent": 12.0,
            "total_trades": 40,
        },
    }
    metrics = metrics_from_payload(payload)
    hit, reason = target_hit(metrics, _target())
    assert hit is True
    assert reason == "all targets met"


def test_target_miss_explains_failed_checks():
    metrics = metrics_from_payload(
        {
            "metrics": {
                "net_profit_percent": 8.0,
                "profit_factor": 1.05,
                "max_drawdown_percent": 40.0,
                "total_trades": 5,
            }
        }
    )
    hit, reason = target_hit(metrics, _target())
    assert hit is False
    assert "net_profit_percent" in reason
    assert "total_trades" in reason


def test_internal_api_ratio_fields_become_percent_points():
    metrics = metrics_from_payload(
        {
            "strategy": "HUB DOGE EMA RSI ATR",
            "metrics": {
                "net_profit": -904.45,
                "net_profit_percent": -0.09044550080397093,
                "profit_factor": 0.9649265441714115,
                "max_drawdown_percent": 0.3066784143550533,
                "total_trades": 436,
                "percent_profitable": 0.26146788990825687,
            },
        }
    )
    assert metrics.net_profit_percent is not None
    assert abs(metrics.net_profit_percent - (-9.044550080397093)) < 1e-9
    assert abs((metrics.max_drawdown_percent or 0) - 30.66784143550533) < 1e-9
    assert abs((metrics.percent_profitable or 0) - 26.146788990825687) < 1e-9
    hit, reason = target_hit(metrics, _target())
    assert hit is False
    assert "net_profit_percent" in reason
    assert "profit_factor" in reason


def test_unix_seconds_to_iso():
    assert unix_to_iso(1789480800) == "2026-09-15T14:00:00Z"


def test_analysis_snapshot_matches_tester_key_stats():
    metrics = metrics_from_payload(
        {
            "strategy": "HUB DOGE EMA RSI ATR",
            "currency": "USDT",
            "metrics": {
                "net_profit": -1030.22,
                "net_profit_percent": -0.1030,
                "max_drawdown": 3809.88,
                "max_drawdown_percent": 0.3067,
                "total_trades": 437,
                "winning_trades": 114,
                "losing_trades": 323,
                "percent_profitable": 0.2609,
                "avg_trade_percent": -0.000236,
                "largest_win_percent": 0.0488,
                "largest_loss_percent": -0.0504,
                "period_from_unix": 1704067200,
                "period_to_unix": 1789480800,
                "period_source": "chart_bars",
                "bar_count": 5000,
            },
        }
    )
    snap = analysis_snapshot(metrics, symbol="BINANCE:DOGEUSDT", timeframe="60")
    assert abs((snap["net_profit_percent"] or 0) - (-10.30)) < 1e-9
    assert abs((snap["max_drawdown_percent"] or 0) - 30.67) < 0.01
    assert abs((snap["win_rate_percent"] or 0) - 26.09) < 0.01
    assert snap["total_trades"] == 437
    assert snap["winning_trades"] == 114
    assert snap["period_start"] == "2024-01-01T00:00:00Z"
    assert snap["period_end"] == "2026-09-15T14:00:00Z"


def test_huge_profit_factor_does_not_outrank_higher_net_profit():
    target = _target()
    keep = metrics_from_payload(
        {
            "metrics": {
                "net_profit_percent": 93.0,
                "profit_factor": 9.9,
                "max_drawdown_percent": 14.0,
                "total_trades": 4,
            }
        }
    )
    two_wins = metrics_from_payload(
        {
            "metrics": {
                "net_profit_percent": 59.0,
                "profit_factor": 373.0,
                "max_drawdown_percent": 14.0,
                "total_trades": 2,
            }
        }
    )
    assert score_metrics(keep, target) > score_metrics(two_wins, target)

