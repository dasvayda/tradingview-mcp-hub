from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Protocol

from hub.chart_prep import is_foreign_strategy
from hub.metrics import metrics_from_payload
from hub.models import HubConfig, StrategyMetrics


class TvClient(Protocol):
    def health(self) -> dict[str, Any]: ...
    def switch_layout(self, name: str) -> dict[str, Any]: ...
    def set_symbol(self, symbol: str) -> dict[str, Any]: ...
    def set_timeframe(self, timeframe: str) -> dict[str, Any]: ...
    def ensure_strategy_editor(self) -> dict[str, Any]: ...
    def new_strategy(self) -> dict[str, Any]: ...
    def remove_foreign_strategies(self) -> list[str]: ...
    def set_pine(self, path: Path) -> dict[str, Any]: ...
    def compile_pine(self) -> dict[str, Any]: ...
    def pine_errors(self) -> dict[str, Any]: ...
    def wait_for_results(self) -> StrategyMetrics: ...
    def screenshot(self, dest_stem: str) -> dict[str, Any]: ...


class TvCliError(RuntimeError):
    def __init__(self, message: str, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.payload = payload or {}


class TvCliClient:
    """Wraps tradesdontlie/tradingview-mcp `tv` CLI."""

    def __init__(self, config: HubConfig) -> None:
        self.config = config

    def _run(self, args: list[str], timeout: int = 60) -> dict[str, Any]:
        command = [*self.config.tv.command, *args]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        payload: dict[str, Any]
        if stdout:
            try:
                parsed = json.loads(stdout)
                payload = parsed if isinstance(parsed, dict) else {"result": parsed}
            except json.JSONDecodeError as exc:
                raise TvCliError(f"tv CLI returned non-JSON: {stdout[:400]}", {"stdout": stdout}) from exc
        else:
            payload = {}
        if completed.returncode != 0:
            message = payload.get("error") or stderr or f"tv exit {completed.returncode}"
            raise TvCliError(str(message), payload)
        if payload.get("success") is False:
            raise TvCliError(str(payload.get("error") or "tv command failed"), payload)
        return payload

    def health(self) -> dict[str, Any]:
        return self._run(["status"])

    def switch_layout(self, name: str) -> dict[str, Any]:
        return self._run(["layout", "switch", name])

    def set_symbol(self, symbol: str) -> dict[str, Any]:
        return self._run(["symbol", symbol])

    def set_timeframe(self, timeframe: str) -> dict[str, Any]:
        return self._run(["timeframe", timeframe])

    def ensure_strategy_editor(self) -> dict[str, Any]:
        try:
            self._run(["ui", "panel", "pine-editor", "open"])
        except TvCliError:
            pass
        try:
            self._run(["ui", "panel", "strategy-tester", "open"])
        except TvCliError:
            pass
        return {"success": True}

    def new_strategy(self) -> dict[str, Any]:
        try:
            return self._run(["pine", "new", "strategy"])
        except TvCliError as exc:
            return {"success": False, "error": str(exc)}

    def chart_studies(self) -> list[dict[str, Any]]:
        try:
            state = self._run(["state"])
        except TvCliError:
            return []
        studies = state.get("studies") or []
        return studies if isinstance(studies, list) else []

    def remove_foreign_strategies(self) -> list[str]:
        if not self.config.tv.clear_existing_strategies:
            return []
        keep = self.config.tv.keep_strategy_substring
        removed: list[str] = []
        for study in self.chart_studies():
            name = str(study.get("name") or "")
            entity_id = str(study.get("id") or "")
            if not entity_id or not is_foreign_strategy(name, keep):
                continue
            try:
                self._run(["indicator", "remove", entity_id])
                removed.append(name)
            except TvCliError:
                continue
        return removed

    def set_pine(self, path: Path) -> dict[str, Any]:
        return self._run(["pine", "set", "--file", str(path)])

    def compile_pine(self) -> dict[str, Any]:
        payload = self._run(["pine", "compile"])
        clicked = payload.get("button_clicked")
        if clicked == "Pine Save" or not payload.get("study_added"):
            # Save would overwrite the currently open saved Pine file.
            fallback = self._click_add_to_chart()
            payload = {
                **payload,
                "overwrite_prevented": clicked == "Pine Save",
                "study_added_fallback": fallback,
            }
        time.sleep(self.config.tv.compile_wait_seconds)
        return payload

    def _click_add_to_chart(self) -> str:
        script = (
            "(function(){ var btns=document.querySelectorAll('button'); "
            "for (var i=0;i<btns.length;i++){ "
            "var t=(btns[i].textContent||'').trim(); "
            "if (/^add to chart$/i.test(t) || /^add to chartadd to chart$/i.test(t)) { "
            "if (btns[i].offsetParent) { btns[i].click(); return 'clicked'; } } } "
            "return 'not_found'; })()"
        )
        try:
            result = self._run(["ui", "eval", script])
            return str(result.get("result") or result.get("value") or result)
        except TvCliError as exc:
            return f"eval_failed:{exc}"

    def pine_errors(self) -> dict[str, Any]:
        return self._run(["pine", "errors"])

    def wait_for_results(self) -> StrategyMetrics:
        last = StrategyMetrics(error="no strategy poll yet")
        retries = max(1, self.config.tv.results_retries)
        for attempt in range(retries):
            if attempt:
                time.sleep(self.config.tv.results_wait_seconds)
            try:
                payload = self._run(["data", "strategy"])
            except TvCliError as exc:
                last = StrategyMetrics(error=str(exc), raw=exc.payload)
                continue
            last = metrics_from_payload(payload)
            if last.ok:
                return last
        return last

    def screenshot(self, dest_stem: str) -> dict[str, Any]:
        return self._run(["screenshot", "--region", "strategy_tester", "--output", dest_stem])


class DryRunTvClient:
    """Offline stand-in so the loop can be tested without TradingView Desktop."""

    SWEET_SPOT = {
        "fast_ema": 12.0,
        "slow_ema": 55.0,
        "rsi_long": 52.0,
        "atr_mult": 2.0,
        "rr_ratio": 2.5,
    }

    def __init__(self, config: HubConfig, params_provider) -> None:
        self.config = config
        self.params_provider = params_provider

    def health(self) -> dict[str, Any]:
        return {"success": True, "mode": "dry-run"}

    def switch_layout(self, name: str) -> dict[str, Any]:
        return {"success": True, "layout": name}

    def set_symbol(self, symbol: str) -> dict[str, Any]:
        return {"success": True, "symbol": symbol}

    def set_timeframe(self, timeframe: str) -> dict[str, Any]:
        return {"success": True, "timeframe": timeframe}

    def ensure_strategy_editor(self) -> dict[str, Any]:
        return {"success": True}

    def new_strategy(self) -> dict[str, Any]:
        return {"success": True}

    def remove_foreign_strategies(self) -> list[str]:
        return []

    def set_pine(self, path: Path) -> dict[str, Any]:
        return {"success": True, "file": str(path)}

    def compile_pine(self) -> dict[str, Any]:
        return {"success": True}

    def pine_errors(self) -> dict[str, Any]:
        return {"success": True, "errors": []}

    def wait_for_results(self) -> StrategyMetrics:
        params = self.params_provider()
        distance = 0.0
        for key, sweet in self.SWEET_SPOT.items():
            current = float(params.get(key, sweet))
            distance += abs(current - sweet) / max(abs(sweet), 1.0)
        profit = max(5.0, 42.0 - distance * 18.0)
        drawdown = min(40.0, 8.0 + distance * 9.0)
        trades = int(max(12, 48 - distance * 10))
        pf = max(0.7, 1.9 - distance * 0.35)
        return StrategyMetrics(
            net_profit=self.config.initial_capital * profit / 100.0,
            net_profit_percent=profit,
            profit_factor=pf,
            max_drawdown_percent=drawdown,
            total_trades=trades,
            percent_profitable=52.0,
            strategy="HUB DOGE EMA RSI ATR",
            currency="USD",
        )

    def screenshot(self, dest_stem: str) -> dict[str, Any]:
        return {"success": True, "skipped": True, "stem": dest_stem}
