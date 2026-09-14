# TradingView MCP Hub

이 레포는 **TradingView Desktop 백테스트를 반복하면서**, 목표 수익률에 가까워지도록 파인스크립트를 고치는 허브임.

## 문서

| 파일 | 역할 | 언제 읽나 |
|------|------|-----------|
| [progress.md](progress.md) | 지금 하는 일, 남은 일, 최근 한 일 | 매 작업 시작 |
| [decisions.md](decisions.md) | 큰 방향 전환 (왜 / 무엇을 안 하는지) | 전략·루프를 바꿀 때 |
| [architecture.md](architecture.md) | 코드가 이렇게 나뉜 이유 | 구조·실행 흐름 |
| 이 파일 (`agent.md`) | 차트 준비, 파인 규칙, 에이전트 습관 | MCP·차트 조작 전 |
| [README.md](README.md) | 소개와 사용법 | 사람 온보딩 |

Cursor Plan 초안만 `.cursor/plans/` 에 둠. 진행·백로그는 `progress.md` 에 적음.

## 쓰는 MCP

GitHub star 기준으로 TradingView MCP 중 가장 많이 쓰인 건 [tradesdontlie/tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp) 임 (약 6천 star).

이 MCP는 로컬 TradingView 앱에 붙어서:

- 종목/타임프레임 바꾸기
- 파인스크립트 넣기 → 컴파일 → 에러 읽기
- Strategy Tester 숫자 읽기 (`data_get_strategy_results`)

를 할 수 있음. 이 허브는 그 도구들을 **정해진 횟수만큼 루프**로 돌림.

프로젝트 MCP 설정은 `.cursor/mcp.json`. Desktop debug 안내는 `python -m hub web` 페이지.

## 차트 준비

레이아웃에 전략이 이미 붙어 있으면 Tester가 그 숫자를 읽음. 파인 에디터에 저장된 스크립트가 열려 있으면 Save가 그 파일을 덮어씀.

1. 범례에서 기존 Strategy를 X로 제거함. 눈 아이콘만 끄면 Tester가 다시 표시할 수 있음.
2. 파인 에디터는 Open → New → Strategy 로 빈 스크립트를 연 뒤 실행함.
3. 허브는 `tv.clear_existing_strategies: true` 이면 이름에 Strategy가 들어간 스터디를 차트에서 제거함.

기존에 오류 없이 돌아가던 전략 원본은 `pinescript/reference/` 에 둔다. 허브 템플릿(`pinescript/doge_ema_rsi_atr.pine`)과 섞지 않는다.

레퍼런스 스크립트 헤더: 1행 `//@version=...`, 2행 `strategy("제목", ...)`. 허브가 차트/테스터에서 전략을 찾을 때도 이 제목 문자열을 씀.

## 루프 습관

1. `BINANCE:DOGEUSDT` 차트를 연다.
2. 허브 템플릿을 넣는다. 지금은 `pinescript/doge_ema_rsi_atr.pine` (베이스가 바뀌면 그 파일).
3. TradingView 백테스트 결과를 읽는다.
4. 목표 미달이면 파라미터 또는 로직을 **하나** 고친다.
5. `loop_limit` 까지 반복한다.

베이스 전략이 정해지기 전에는 이 루프를 본 작업으로 쓰지 않음. 현재 초점과 남은 일은 [progress.md](progress.md), 방향은 [decisions.md](decisions.md).
