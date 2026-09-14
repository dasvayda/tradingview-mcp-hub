from hub.metrics import metrics_from_payload, target_hit
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
