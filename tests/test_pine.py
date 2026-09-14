from hub.config import load_config
from hub.pine import apply_params, extract_params


def test_extract_and_patch_hub_tags():
    source = load_config().pine.source_path.read_text(encoding="utf-8")
    params = extract_params(source)
    assert params["fast_ema"] == 8
    assert params["slow_ema"] == 89
    assert params["atr_mult"] == 1.2
    updated = apply_params(source, {"fast_ema": 12, "atr_mult": 2.0, "allow_short": 0})
    patched = extract_params(updated)
    assert patched["fast_ema"] == 12
    assert patched["atr_mult"] == 2.0
    assert patched["allow_short"] == 0
    assert 'input.int(12, "Fast EMA"' in updated
    assert "input.float(2.0," in updated
    assert "input.bool(false," in updated
