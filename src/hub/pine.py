from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

HUB_TAG = re.compile(
    r"^(?P<indent>\s*)(?P<lhs>.+?=\s*input\.(?P<kind>int|float|bool)\()"
    r"(?P<value>true|false|-?\d+(?:\.\d+)?)"
    r"(?P<rest>.*?)\s*//\s*HUB:(?P<name>[A-Za-z0-9_]+)\s*$",
    re.MULTILINE,
)


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_params(source: str) -> dict[str, float]:
    params: dict[str, float] = {}
    for match in HUB_TAG.finditer(source):
        raw = match.group("value")
        if raw in {"true", "false"}:
            params[match.group("name")] = 1.0 if raw == "true" else 0.0
        else:
            params[match.group("name")] = float(raw)
    return params


def _format_value(kind: str, value: float) -> str:
    if kind == "bool":
        return "true" if float(value) >= 0.5 else "false"
    if kind == "int":
        return str(int(round(float(value))))
    number = float(value)
    if number.is_integer():
        return f"{int(number)}.0"
    return f"{number:g}"


def apply_params(source: str, params: Mapping[str, float]) -> str:
    def repl(match: re.Match[str]) -> str:
        name = match.group("name")
        if name not in params:
            return match.group(0)
        formatted = _format_value(match.group("kind"), params[name])
        return (
            f"{match.group('indent')}{match.group('lhs')}{formatted}"
            f"{match.group('rest')}  // HUB:{name}"
        )

    return HUB_TAG.sub(repl, source)


def write_source(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def snapshot_with_params(template: str, params: Mapping[str, float], dest: Path) -> str:
    updated = apply_params(template, params)
    write_source(dest, updated)
    return updated
