# TradingView MCP Hub

Pine strategy를 TradingView Strategy Tester에 넣고, 목표 수익률까지 백테스트를 반복하는 샘플 허브.

문서: 지금/남은 일 [progress.md](progress.md), 방향 전환 [decisions.md](decisions.md), 에이전트 규칙 [agent.md](agent.md), 구조 [architecture.md](architecture.md).

## 준비

1. TradingView Desktop + 유효 구독
2. `vendor/README.md` 대로 MCP clone + `npm install` (이미 있으면 생략)
3. Cursor에서 프로젝트 MCP `tradingview` 활성화 (`.cursor/mcp.json`)
4. debug 연동 페이지에서 Desktop 연결 확인

```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m hub web
```

브라우저에서 http://127.0.0.1:8788 를 열고, debug 실행 방법과 연결 상태를 확인함.

```bash
.\.venv\Scripts\python.exe -m hub status --dry-run
.\.venv\Scripts\python.exe -m hub run --dry-run
.\.venv\Scripts\python.exe -m pytest
```

실차트 루프:

```bash
python -m hub run --config config/default.yaml
```

Cursor에서 에이전트 루프를 돌리려면 skill `tv-backtest-loop` 를 사용. `config/default.yaml` 의 `mutation.mode` 를 `agent` 로 바꾸면 Python은 1회 백테스트만 하고, 파인 수정은 에이전트가 담당함.

## 설정

| 키 | 기본 | 의미 |
|----|------|------|
| `symbol` | `BINANCE:DOGEUSDT` | 차트 심볼 |
| `timeframe` | `60` | 1시간 |
| `layout` | (비움) | 저장 레이아웃 이름. 비우면 현재 차트 |
| `loop_limit` | `20` | 최대 반복 |
| `target.net_profit_percent` | `20` | 목표 순수익 % |

## 주의

이 도구는 로컬 TradingView 앱을 조작함. 실거래 봇이 아니고, 과거 백테스트 숫자를 목표에 맞추는 연습용 루프임. 과최적화(한 구간만 잘 맞는 파라미터) 위험이 있음.
