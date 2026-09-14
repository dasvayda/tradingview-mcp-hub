from hub.mutate import ParamSearch, clamp_pair, fingerprint


def test_search_skips_seen_and_keeps_fast_below_slow():
    knobs = {
        "fast_ema": (8.0, 12.0),
        "slow_ema": (26.0, 55.0),
        "atr_mult": (1.2, 1.5),
    }
    search = ParamSearch(knobs, seed=1)
    start = {"fast_ema": 8.0, "slow_ema": 26.0, "atr_mult": 1.2}
    search.mark(start)
    nxt = search.next_candidate(start)
    assert nxt is not None
    assert fingerprint(nxt) != fingerprint(start)
    assert nxt["fast_ema"] < nxt["slow_ema"]


def test_clamp_pair_pushes_slow_above_fast():
    fixed = clamp_pair({"fast_ema": 55.0, "slow_ema": 26.0})
    assert fixed["slow_ema"] > fixed["fast_ema"]
