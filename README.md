# TradingView MCP Hub

Cursor가 **TradingView Desktop Strategy Tester** 를 직접 돌리게 하는 허브.

파인 전략을 차트에 넣고, 테스터 숫자를 읽고, 목표에 가까워질 때까지 한 칸만 고친다.
가격 CSV를 따로 긁어서 우리만의 시뮬을 돌리지 않는다. 점수는 쓰는 차트 앱 안에 있다.

## MCP

차트에 붙는 손은 [tradesdontlie/tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp) 임. MIT 라이선스. TradingView Desktop 을 CDP로 조종해서 종목·시간봉을 바꾸고, 파인을 넣고, Strategy Tester 숫자를 읽음.

이 레포는 그 MCP를 클론해 쓰고, 그 위에 **반복 루프 / YAML 설정 / 채점** 만 얹음. 클론은 `vendor/tradingview-mcp/` 에 두며 git에는 넣지 않음. 설치는 아래 Usage.

TradingView Inc. 공식 도구가 아님. 로컬 Desktop 이 debug 포트로 켜져 있어야 함.

## 한 바퀴

1. 종목과 시간봉을 `config` 에서 고른다. 기본은 `BINANCE:DOGEUSDT` 1시간.
2. 허브가 차트에 붙은 다른 Strategy를 치우고, 파인 스크립트를 넣는다.
3. Strategy Tester 의 순이익, 손익비, 낙폭, 거래 수를 읽는다.
4. 목표면 멈춘다. 아니면 파라미터 하나, 또는 로직 한 줄을 고치고 다시 넣는다.

파라미터만 돌리는 모드와, Cursor가 진입·청산을 고치는 모드가 있음. 한 사이클에 가설은 하나. 여러 필터를 한 번에 쌓지 않음.

## 이 레포가 아닌 것

실거래 봇이 아님. 주문 API도 없음. TradingView가 보여 주는 과거 성적에 맞춰 파인 스크립트를 다듬는 연습용 루프임. 한 구간에만 예쁜 숫자는 과최적화일 수 있음.

## 문서

| 파일 | 내용 |
|------|------|
| [progress.md](progress.md) | 지금 하는 일, 남은 일 |
| [ledger.md](ledger.md) | 백테스트 날짜·커밋·가설·성적 |
| [decisions.md](decisions.md) | 큰 방향과, 하지 않기로 한 것 |
| [architecture.md](architecture.md) | 코드가 이렇게 나뉜 이유 |
| [agent.md](agent.md) | 차트·파인·MCP 를 만질 때 규칙 |

---

## Usage

### Requirements

- TradingView Desktop 과 백테스트를 돌릴 수 있는 구독
- Python 3.10+, Node.js (MCP)
- Cursor (에이전트 루프를 쓸 때)

### Setup

```bash
git clone https://github.com/dasvayda/tradingview-mcp-hub.git
cd tradingview-mcp-hub
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
git clone --depth 1 https://github.com/tradesdontlie/tradingview-mcp.git vendor/tradingview-mcp
cd vendor/tradingview-mcp
npm install
cd ../..
```

TradingView 는 debug 포트 `9222` 로 켜야 MCP가 붙음. 안내는 `python -m hub web` → http://127.0.0.1:8788 . Windows 면 `scripts/launch_tv_debug.ps1` 도 있음.

Cursor 에서 이 폴더를 연 뒤 프로젝트 MCP `tradingview` 를 켜면 됨. 설정 예시는 `.cursor/mcp.json`.

차트: 파인 에디터는 **Open → New → Strategy**. 저장된 스크립트가 열린 채로 Save 하면 그 파일을 덮어씀. 범례의 다른 Strategy 는 X 로 지움 (눈 아이콘만 끄면 Tester가 다시 켤 수 있음).

### Run

연결만 확인:

```powershell
.\.venv\Scripts\python.exe -m hub status
```

Desktop 없이 루프 뼈대만:

```powershell
.\.venv\Scripts\python.exe -m hub run --dry-run
```

실차트 1회 스모크, 이후 본 루프:

```powershell
.\.venv\Scripts\python.exe -m hub run --config config/live-smoke.yaml
.\.venv\Scripts\python.exe -m hub run --config config/default.yaml
```

`mutation.mode: params` 면 Python이 `HUB:` 태그가 붙은 input 만 바꿈. `agent` 면 백테스트 1회 후 멈추고, Cursor skill `tv-backtest-loop` 가 파인을 고침.

테스트:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

### Config

`config/default.yaml`

| 키 | 기본 | 의미 |
|----|------|------|
| `symbol` | `BINANCE:DOGEUSDT` | 차트 심볼 |
| `timeframe` | `60` | 1시간 |
| `layout` | `crypto` | 저장 레이아웃. 비우면 지금 차트 |
| `loop_limit` | `20` | 최대 반복 |
| `target.net_profit_percent` | `20` | 목표 순이익 % |

로컬에서만 바꿀 값은 `config/local.yaml` 에 두면 됨. 이 파일은 git 에 안 들어감.
