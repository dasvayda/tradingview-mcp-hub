from hub.chart_prep import is_foreign_strategy


def test_keeps_hub_strategy_and_drops_others():
    assert is_foreign_strategy("Daily MA Strategy v1.0") is True
    assert is_foreign_strategy("HUB DOGE EMA RSI ATR") is False
    assert is_foreign_strategy("Volume") is False
    assert is_foreign_strategy("Smart Money Concepts [LuxAlgo]") is False
