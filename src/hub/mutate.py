from __future__ import annotations

import hashlib
import random
from typing import Mapping, Sequence

ParamMap = dict[str, float]


def fingerprint(params: Mapping[str, float]) -> str:
    packed = ",".join(f"{k}={params[k]:.6g}" for k in sorted(params))
    return hashlib.sha1(packed.encode("utf-8")).hexdigest()[:12]


def clamp_pair(params: ParamMap) -> ParamMap:
    updated = dict(params)
    fast = updated.get("fast_ema")
    slow = updated.get("slow_ema")
    if fast is not None and slow is not None and fast >= slow:
        updated["slow_ema"] = fast + 8
    ma_fast = updated.get("ma_len")
    ma_slow = updated.get("ma_len_slow")
    if ma_fast is not None and ma_slow is not None and ma_fast >= ma_slow:
        updated["ma_len_slow"] = ma_fast + 20
    return updated


def neighbors(params: ParamMap, knobs: Mapping[str, tuple[float, ...]], rng: random.Random) -> list[ParamMap]:
    options: list[ParamMap] = []
    names = [name for name in knobs if name in params]
    rng.shuffle(names)
    for name in names:
        grid = knobs[name]
        current = params[name]
        try:
            index = min(range(len(grid)), key=lambda i: abs(grid[i] - current))
        except ValueError:
            continue
        for delta in (-1, 1):
            next_index = index + delta
            if 0 <= next_index < len(grid):
                candidate = clamp_pair({**params, name: grid[next_index]})
                options.append(candidate)
    return options


def random_from_knobs(
    base: ParamMap,
    knobs: Mapping[str, tuple[float, ...]],
    rng: random.Random,
) -> ParamMap:
    rolled = dict(base)
    for name, grid in knobs.items():
        if grid:
            rolled[name] = rng.choice(grid)
    return clamp_pair(rolled)


class ParamSearch:
    def __init__(
        self,
        knobs: Mapping[str, tuple[float, ...]],
        seed: int,
        banned_matches: Sequence[Mapping[str, float]] | None = None,
    ) -> None:
        self.knobs = knobs
        self.rng = random.Random(seed)
        self.seen: set[str] = set()
        self.banned_matches = [dict(item) for item in banned_matches or []]

    def mark(self, params: Mapping[str, float]) -> None:
        self.seen.add(fingerprint(params))

    def _usable(self, params: ParamMap) -> bool:
        from hub.ledger import params_match_ban

        if fingerprint(params) in self.seen:
            return False
        return not any(params_match_ban(params, match) for match in self.banned_matches)

    def next_candidate(self, current: ParamMap) -> ParamMap | None:
        for candidate in neighbors(current, self.knobs, self.rng):
            if self._usable(candidate):
                self.seen.add(fingerprint(candidate))
                return candidate
        for _ in range(24):
            candidate = random_from_knobs(current, self.knobs, self.rng)
            if self._usable(candidate):
                self.seen.add(fingerprint(candidate))
                return candidate
        return None
