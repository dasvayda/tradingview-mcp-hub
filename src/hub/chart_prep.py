from __future__ import annotations


def is_foreign_strategy(name: str, keep_substring: str = "HUB DOGE") -> bool:
    """True when a chart study looks like a strategy that is not the hub script."""
    text = (name or "").strip()
    if not text:
        return False
    lowered = text.lower()
    keep = (keep_substring or "").strip().lower()
    if keep and keep in lowered:
        return False
    return "strategy" in lowered
