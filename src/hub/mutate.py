from __future__ import annotations

import hashlib
import random
from typing import Mapping

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
    def __init__(self, knobs: Mapping[str, tuple[float, ...]], seed: int) -> None:
        self.knobs = knobs
        self.rng = random.Random(seed)
        self.seen: set[str] = set()

    def mark(self, params: Mapping[str, float]) -> None:
        self.seen.add(fingerprint(params))

    def next_candidate(self, current: ParamMap) -> ParamMap | None:
        for candidate in neighbors(current, self.knobs, self.rng):
            key = fingerprint(candidate)
            if key not in self.seen:
                self.seen.add(key)
                return candidate
        for _ in range(24):
            candidate = random_from_knobs(current, self.knobs, self.rng)
            key = fingerprint(candidate)
            if key not in self.seen:
                self.seen.add(key)
                return candidate
        return None
