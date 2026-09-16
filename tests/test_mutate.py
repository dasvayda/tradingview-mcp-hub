from hub.mutate import ParamSearch, clamp_pair, fingerprint


def test_search_skips_banned_reclaim_loosening():
    knobs = {
        "reclaim_pct": (1.005, 1.015, 1.03),
        "atr_mult": (2.0, 2.5),
    }
    search = ParamSearch(knobs, seed=1, banned_matches=[{"reclaim_pct": 1.005}])
    start = {"reclaim_pct": 1.015, "atr_mult": 2.0}
    search.mark(start)
    seen_reclaim = set()
    current = start
    for _ in range(8):
        nxt = search.next_candidate(current)
        if nxt is None:
            break
        seen_reclaim.add(nxt["reclaim_pct"])
        current = nxt
    assert 1.005 not in seen_reclaim
    assert seen_reclaim


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


def test_clamp_pair_pushes_slow_ma_above_fast():
    fixed = clamp_pair({"ma_len": 89.0, "ma_len_slow": 50.0})
    assert fixed["ma_len_slow"] > fixed["ma_len"]
