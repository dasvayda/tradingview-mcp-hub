# Backtest ledger

파인이나 파라미터를 바꾸기 **전에** 이 파일과 `ledger.jsonl` 을 읽음.
`verdict: reject` 의 `ban.match` 와 같은 변경은 새 근거 없이 다시 하지 않음.
Keep 비교는 **같은 종목** 끼리만 함. 런타임 `runs/` 로그는 git에 안 남음.

## Keep (종목별 베스트)

### `BINANCE:DOGEUSDT`

- id: `20260916T174612Z`
- date: 2026-09-16T17:46:12Z
- commit: `c5be91a dirty`
- strategy: HUB DOGE Daily MA Reclaim
- change: ma_len 50.0 -> 89.0
- result: NP 93.36%  PF 9.968  MDD 14.27%  trades 4
- lesson: Slower fast MA. NP 66% -> 93%, PF 2.41 -> 9.97, MDD 27% -> 14%, but trades 7 -> 4. New keep; still far from min_trades 20.

### `BINANCE:HYPEUSDT.P`

- id: `20260916T180130Z`
- date: 2026-09-16T18:01:30Z
- commit: `c5be91a dirty`
- strategy: HUB DOGE Daily MA Reclaim
- change: first test on BINANCE:HYPEUSDT.P
- result: NP 90.69%  PF 11.754  MDD 14.74%  trades 5
- lesson: Same Keep pine on HYPE perp. NP +90.7% PF 11.8 MDD 14.7% trades 5. Period starts 2025-05-30 (listed later than DOGE). Buy-and-hold +74%.

### `BINANCE:ZECUSDT`

- id: `20260916T175730Z`
- date: 2026-09-16T17:57:30Z
- commit: `c5be91a dirty`
- strategy: HUB DOGE Daily MA Reclaim
- change: first test on BINANCE:ZECUSDT
- result: NP 66.83%  PF 2.250  MDD 29.75%  trades 11
- lesson: Same Keep pine on ZEC. NP +66.8% PF 2.25 MDD 29.7% trades 11. Beat buy-and-hold +22%. First ZEC keep; not compared to DOGE NP.

## Do not retry

| date | symbol | commit | change | why | ban.match |
|------|--------|--------|--------|-----|-----------|
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a` | ta.crossover/ta.crossunder inside and | Assign crossUp/crossDown on their own lines before using them in conditions. | `crossover_in_and` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a` | compile while Daily MA still on chart / saved pine open | Remove other Strategy studies with X. Pine Editor must be New Strategy so Save does not overwrite a saved file. | `wrong_tester_strategy` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a` | family=1h EMA crossover (fast 8 / slow 89 / RSI 58-45 / ATR 1.2 / RR 1.5) | Do not use 1h EMA crossover as the base family. 437 trades, NP -10.30%, PF 0.96, MDD 30.67% on tester 2025-01-01 to 2026-09-16. | `1h_ema_crossover` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | reclaim_pct 1.015 -> 1.005 | Trades 7->13 but MDD 27->38. Do not loosen reclaim_pct to chase min_trades. | `{"reclaim_pct": 1.005}` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | cooldown_days 2 -> 1 (reclaim_pct stays 1.015) | NP 66% -> 38% with only two extra trades. Do not cut cooldown_days to 1 from this keep. | `{"cooldown_days": 1.0}` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | atr_mult 2.0 -> 2.5 | Wider ATR stop. Same 7 trades but NP 66% -> 1.9% and PF 1.05. Do not raise atr_mult to 2.5 from this keep. | `{"atr_mult": 2.5}` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | atr_mult 2.0 -> 1.5 | Tighter ATR stop. PF 2.42->2.63 and MDD 27->24 but NP 66%->60%. Keep the 2.0 stop. | `{"atr_mult": 1.5}` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | rr_ratio 2.0 -> 2.5 | Higher target. Same 7 trades but NP 66% -> -1.1% and PF 0.97. Do not raise rr_ratio to 2.5 from this keep. | `{"rr_ratio": 2.5}` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | rr_ratio 2.0 -> 1.5 | Lower target. NP 66% -> 54%, PF 2.42 -> 2.27. Keep rr_ratio 2.0. | `{"rr_ratio": 1.5}` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | invalid_pct 0.985 -> 0.97 | Looser MA-fail exit. Same 7 trades, NP 66% -> 62%. Keep invalid_pct 0.985. | `{"invalid_pct": 0.97}` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | ma_len 50.0 -> 34.0 | Faster daily MA. Trades 7->13 but NP 66% -> -2.2% and MDD 36%. Do not drop ma_len to 34. | `{"ma_len": 34.0}` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | ma_len_slow 100.0 -> 150.0 | Spacing slow MA to 150. NP 93% -> 78%, PF 10 -> 3.3. Keep slow MA 100 with fast 89. | `{"ma_len_slow": 150.0}` |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | reclaim_pct 1.015 -> 1.03 | Tighter reclaim. Only 2 wins, NP 93% -> 59%. PF 373 is no-loser noise. Do not raise reclaim_pct to 1.03. | `{"reclaim_pct": 1.03}` |

## Chronology

| date | symbol | commit | change | NP% | PF | MDD% | trades | verdict |
|------|--------|--------|--------|-----|----|------|--------|---------|
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a` | ta.crossover/ta.crossunder inside and | ? | ? | ? | ? | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a` | compile while Daily MA still on chart / saved pine open | ? | ? | ? | ? | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a` | family=1h EMA crossover (fast 8 / slow 89 / RSI 58-45 / ATR 1.2 / RR 1.5) | -10.30 | 0.960 | 30.67 | 437 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | new pine family doge_daily_ma_reclaim; reclaim_pct 1.015, cooldown_days 2, atr_mult 2, rr_ratio 2 | 66.43 | 2.415 | 26.97 | 7 | keep |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | reclaim_pct 1.015 -> 1.005 | 63.29 | 1.702 | 37.81 | 13 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | cooldown_days 2 -> 1 (reclaim_pct stays 1.015) | 38.08 | 1.549 | 26.97 | 9 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | atr_mult 2.0 -> 2.5 | 1.92 | 1.047 | 29.83 | 7 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | atr_mult 2.0 -> 1.5 | 59.99 | 2.625 | 24.10 | 8 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | rr_ratio 2.0 -> 2.5 | -1.13 | 0.974 | 31.93 | 7 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | rr_ratio 2.0 -> 1.5 | 53.96 | 2.271 | 24.10 | 8 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | invalid_pct 0.985 -> 0.97 | 61.93 | 2.280 | 26.97 | 7 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | ma_len 50.0 -> 34.0 | -2.19 | 0.981 | 36.09 | 13 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | invalid_pct 0.985 -> 0.99 | 66.43 | 2.415 | 26.97 | 7 | note |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | ma_len 50.0 -> 89.0 | 93.36 | 9.968 | 14.27 | 4 | keep |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | ma_len_slow 100.0 -> 150.0 | 78.33 | 3.329 | 23.01 | 5 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | reclaim_pct 1.015 -> 1.03 | 59.32 | 373.329 | 14.27 | 2 | reject |
| 2026-09-16 | `BINANCE:DOGEUSDT` | `c5be91a dirty` | lookback_days 10.0 -> 14.0 | 93.36 | 9.968 | 14.27 | 4 | note |
| 2026-09-16 | `BINANCE:ZECUSDT` | `c5be91a dirty` | first test on BINANCE:ZECUSDT | 66.83 | 2.250 | 29.75 | 11 | keep |
| 2026-09-16 | `BINANCE:HYPEUSDT` | `c5be91a dirty` | first test on BINANCE:HYPEUSDT | 90.69 | 11.754 | 14.74 | 5 | note |
| 2026-09-16 | `BINANCE:HYPEUSDT.P` | `c5be91a dirty` | first test on BINANCE:HYPEUSDT.P | 90.69 | 11.754 | 14.74 | 5 | keep |
