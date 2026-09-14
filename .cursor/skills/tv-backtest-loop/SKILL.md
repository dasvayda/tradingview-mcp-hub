---
name: tv-backtest-loop
description: >-
  Loops TradingView Pine strategy backtests toward a target return using
  tradesdontlie tradingview-mcp (pine inject/compile, Strategy Tester metrics)
  and this repo's Python hub. Use when the user asks to backtest, optimize,
  or loop-edit a Pine strategy, especially DOGEUSDT / Dogecoin.
---

# TradingView backtest optimize loop

Read [agent.md](../../../agent.md), [progress.md](../../../progress.md), [decisions.md](../../../decisions.md), [architecture.md](../../../architecture.md), and `config/default.yaml` before acting.

If `progress.md` says the parameter loop is not the current job, do not run `loop_limit` as the main task. Follow **다음** there instead.

If Desktop CDP is down, open `python -m hub web` (http://127.0.0.1:8788) and follow debug steps. Project MCP config: `.cursor/mcp.json`.

Primary MCP: **tradesdontlie/tradingview-mcp** (highest-star TradingView MCP). Tools:

1. `tv_health_check` — Desktop + CDP must be up
2. `chart_set_symbol` / `chart_set_timeframe` — from config
3. `pine_set_source` → `pine_smart_compile` → `pine_get_errors`
4. `ui_open_panel` `strategy-tester` if the report is empty
5. `data_get_strategy_results` (then `data_get_trades`, `data_get_equity` if needed)
6. `capture_screenshot` region `strategy_tester` only when a visual check helps

Do **not** invent a local backtest engine. The score is TradingView Strategy Tester.

## Config

Load `config/default.yaml` (or the path the user named).

- Default symbol: `BINANCE:DOGEUSDT`
- Optional `layout`: switch to that saved layout first, then apply symbol/timeframe
- Before inject: remove other chart studies whose name contains `Strategy` (hide is not enough)
- Pine Editor must be a **new untitled strategy**. Saving over an open saved script overwrites that file.
- Stop when ALL target fields pass, or when `loop_limit` is reached
- `mutation.mode: params` → run `python -m hub run`
- `mutation.mode: agent` → you edit Pine; Python/`run --dry-run` is optional helper

## Cycle (agent mode)

One hypothesis, one code change, one backtest. Inspired by DaviddTech strategy-optimizer: do not stack filters in a single cycle.

Copy this checklist:

```
[ ] 1. Read config + current pine (pinescript/current.pine if it exists, else source_path)
[ ] 2. Health check TradingView MCP
[ ] 3. Set symbol + timeframe
[ ] 4. Inject pine, compile, fix compile errors only (does not count as the strategy change)
[ ] 5. Read strategy metrics
[ ] 6. If target hit: write runs/report, stop
[ ] 7. If loop_limit hit: keep best, stop
[ ] 8. Else: name the weakness, change ONE thing, save pine, next cycle
```

## What to change

Prefer in this order:

1. Stops / targets (`atr_mult`, `rr_ratio`)
2. Trend lengths (`fast_ema`, `slow_ema`) keep fast < slow
3. RSI gates
4. Only then entry logic (one filter)

Reject a change if trades collapse below `target.min_trades` or MDD blows past `max_drawdown_percent`.

## Output each cycle

Write `runs/cycles.jsonl` append-only if the Python hub is not already logging. After stop, write `runs/report-*.md` with symbol, iterations, best params, metrics, and the last hypothesis.

If MCP is disconnected, say so and offer `python -m hub run --dry-run` for the skeleton loop, or `python -m hub run` once `tv` CLI works.
