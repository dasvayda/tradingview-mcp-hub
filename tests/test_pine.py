from hub.config import load_config
from hub.pine import apply_params, extract_params


def test_extract_and_patch_hub_tags():
    source = load_config().pine.source_path.read_text(encoding="utf-8")
    params = extract_params(source)
    assert params["ma_len"] == 89
    assert "atr_mult" in params
    updated = apply_params(source, {"ma_len": 34, "atr_mult": 3.0, "allow_long": 0})
    patched = extract_params(updated)
    assert patched["ma_len"] == 34
    assert patched["atr_mult"] == 3.0
    assert patched["allow_long"] == 0
    assert 'input.int(34, "MA Length"' in updated
    assert "input.float(3.0," in updated
    assert "input.bool(false," in updated
