# Progress

에이전트는 작업 시작 때 이 파일을 읽음. **지금 / 다음** 만 길게 유지하고, 끝난 일은 아래로 짧게 내림.

큰 방향이 바뀌면 여기 체크만 고치고, 이유·기각은 [decisions.md](decisions.md) 에 적음.

## 지금

TradingView Desktop 연동과 1회 스모크는 됨. 테스터가 `HUB DOGE EMA RSI ATR` 을 읽음.

허브 템플릿은 아직 범용 이평 교차라서, 파라미터 20회 루프는 **본 작업이 아님**. DOGE에 맞는 전략 가문 하나를 고르는 중.

## 다음

1. [ ] 시간봉 고정: config `60`(1시간) 유지 vs 일봉 Daily MA. 한 줄로 결정하고 [decisions.md](decisions.md) 에 적음.
2. [ ] 고른 봉 기준 DOGE 성격 메모 (급등/횡보/거래량). 차트·테스터로 확인 가능한 문장만.
3. [ ] 전략 가문 3~5개 표 비교 후 **베이스 1개** 선택. 교집합으로 합치지 않음.
4. [ ] 리스크 규칙 1~2개만 공통으로 가져옴 (손절, 횡보 회피 등).
5. [ ] 베이스 파인을 `pinescript/` 허브 템플릿으로 교체. `HUB:` 태그는 그 가문 손잡이만.
6. [ ] 테스터 퍼센트 단위 버그 수정 (0.09 = 9%). 그 다음 1회 스모크.
7. [ ] 베이스 + 단위 수정 이후에만 `config/default.yaml` 루프 재개. 한 사이클에 가설 하나.

완료 조건: 베이스 이름·시간봉·고른 이유가 `progress.md` 지금 칸과 `decisions.md` 에 있고, 스모크 전략 이름에 `HUB DOGE` 가 들어감.

## 나중

원본 MCP 스킬은 아직 다양하게 쓰지 않음. 허브 스킬은 주입→컴파일→테스터 숫자에 가깝고, `architecture.md` 가 `strategy-report` 형식만 언급함.

- [ ] `vendor/tradingview-mcp/skills/` 와 `agents/` 를 읽고, 허브에 가져올 것/안 가져올 것을 표로 남김.
  - skills: `chart-analysis`, `pine-develop`, `strategy-report`, `multi-symbol-scan`, `replay-practice`
  - agents: `performance-analyst`
  - 쓸 만하면 `.cursor/skills/` 또는 `tv-backtest-loop` 에 연결. 안 쓰면 [decisions.md](decisions.md) 에 왜 빼는지 한 줄.

## 막힌 것

없음. Desktop CDP는 최근 스모크 때 연결됨.

## 최근에 한 일

- 2026-09-15: 공개 GitHub README 작성, 시크릿/로컬 설정 gitignore 보강.
- 2026-09-15: 문서 체계를 `progress.md` + `decisions.md` 로 나눔. `.cursor/plans/` 백로그는 이쪽으로 옮김.
- 2026-09-15: live-smoke 1회. Daily MA 제거, 허브 전략 테스터 연동 성공. NP ~-9%, PF 0.96, MDD ~31%, 거래 436.
- 2026-09-15: 레퍼런스 파인 `pinescript/reference/` (Daily MA, SOXL Daily MA). 허브 헤더 1행 version / 2행 strategy 제목.
- 2026-09-14: tradesdontlie MCP, Python 허브, debug 웹, `crypto` 레이아웃, 기존 Strategy 자동 제거.
