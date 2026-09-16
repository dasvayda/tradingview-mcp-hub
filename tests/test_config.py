from pathlib import Path

from hub.config import load_config


def test_default_config_uses_doge_usdt():
    config = load_config()
    assert config.symbol == "BINANCE:DOGEUSDT"
    assert config.timeframe == "60"
    assert config.loop_limit >= 1
    assert config.mutation.mode in {"params", "agent"}
    assert "ma_len" in config.mutation.knobs
    assert 1.005 not in config.mutation.knobs.get("reclaim_pct", ())
    assert 1.03 not in config.mutation.knobs.get("reclaim_pct", ())
    assert 2.5 not in config.mutation.knobs.get("atr_mult", ())
    assert 2.5 not in config.mutation.knobs.get("rr_ratio", ())
    assert 34 not in config.mutation.knobs.get("ma_len", ())
    assert config.pine.source_path.exists()
    assert config.layout == "crypto"
    assert config.ledger_jsonl.name == "ledger.jsonl"
    assert config.ledger_md.name == "ledger.md"
    assert config.tv.clear_existing_strategies is True
    assert config.tv.cdp_port == 9222
    assert "vendor" in "".join(config.tv.command) or config.tv.command[0] in {"node", "tv"}


def test_loop_limit_must_be_positive(tmp_path: Path):
    yaml_path = tmp_path / "bad.yaml"
    yaml_path.write_text("symbol: BINANCE:DOGEUSDT\nloop_limit: 0\n", encoding="utf-8")
    try:
        load_config(yaml_path)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "loop_limit" in str(exc)


def test_layout_name_is_optional(tmp_path: Path):
    yaml_path = tmp_path / "layout.yaml"
    yaml_path.write_text(
        "symbol: BINANCE:DOGEUSDT\nlayout: HUB-DOGE-BT\nloop_limit: 3\n",
        encoding="utf-8",
    )
    config = load_config(yaml_path)
    assert config.layout == "HUB-DOGE-BT"
