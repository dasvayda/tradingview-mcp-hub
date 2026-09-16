# Progress

에이전트는 작업 시작 때 이 파일과 [ledger.md](ledger.md) 를 읽음. **지금 / 다음** 만 길게 유지하고, 끝난 일은 아래로 짧게 내림.

실험 숫자·커밋·기각 이유는 ledger. 큰 방향은 [decisions.md](decisions.md).

## 지금

허브 템플릿은 `pinescript/doge_daily_ma_reclaim.pine`. 차트 1시간, 신호는 일봉 HA 이평 재탈환.

**Keep (DOGE):** reclaim 1.015, cooldown 2일, ATR×2 / RR 2, MA 89/100. NP **+93.4%**, PF 9.97, MDD 14%, 거래 4.

**Keep (ZEC):** 같은 파인. NP **+66.8%**, PF 2.25, MDD 30%, 거래 11. 단순 보유 +22%.

**Keep (HYPE perp):** 같은 파인. NP **+90.7%**, PF 11.8, MDD 15%, 거래 5. 구간은 2025-05-30부터 (상장 시점). 단순 보유 +74%.

같은 날 추가 스모크: invalid 0.99(효과 없음), slow 150(기각), reclaim 1.03(기각, PF 왜곡), lookback 14(효과 없음).

## DOGE 1시간 성격

심볼 `BINANCE:DOGEUSDT`. 봉: Binance 1시간 8000개, 2025-10-17 ~ 2026-09-15 UTC.

- 한 시간의 고저 폭 중앙값 **0.80%**. 폭이 1%보다 작은 시간이 **64.6%**. 3% 이상은 **2.7%**.
- 이평 교차 스모크: 거래 437, NP -10.3%, MDD 30.7%.
- 재탈환 Keep: MA 89, 수수료 0.1%인데도 NP +93.4% (거래 4).

## 다음

1. [x] 시간봉 고정: 1시간(`60`) 유지.
2. [x] DOGE 1시간 성격 메모.
3. [x] 베이스: 일봉 이평 재탈환.
4. [x] 리스크 규칙: ATR 스톱/목표 + 일봉 이평 이탈 청산. 일 단위 진입.
5. [x] 허브 파인 교체. 제목 `HUB DOGE Daily MA Reclaim`.
6. [x] 퍼센트 단위 수정.
7. [x] 실험 기억: `ledger.md` / `ledger.jsonl` + reject 재시도 금지.
8. [ ] 거래 수 20 vs 수익 유지. Keep은 4거래. 느슨한 진입으로 20을 맞추지 않음.
9. [x] Keep 주변 손절/목표/이평/재탈환/lookback 스모크.

## 나중

- [ ] `vendor/tradingview-mcp/skills/` 와 `agents/` 를 읽고, 허브에 가져올 것/안 가져올 것을 표로 남김.

## 막힌 것

없음. 파라미터 이웃은 거의 소진. 다음 큰 결정은 거래 수 목표.

## 최근에 한 일

- 2026-09-17: `BINANCE:HYPEUSDT.P` 스모크 NP +90.7% / 5거래. 구간은 2025-05-30부터.
- 2026-09-17: atr/rr/invalid/ma34 스모크 기각. 그때 Keep은 MA 50 +66%.
- 2026-09-17: 백테스트 ledger.
- 2026-09-15: 테스터 Key stats 스키마. 교차 스모크 -10.30% = TV 화면.
- 2026-09-15: 베이스 가문 = 일봉 이평 재탈환.
- 2026-09-14: tradesdontlie MCP, Python 허브, debug 웹.
