# Architecture

Alpha Flow AI is a modular pipeline that ingests institutional options flow, enriches it with market context, and routes signals into actionable queues.

## Components

- **Data Layer (`src/data`)**: Unified Massive/Polygon provider (prices, options flow, greeks) and Benzinga (news). Cached via TTL to avoid redundant pulls.
- **Engines (`src/engines`)**:
  - `MarketRegimeEngine`: derives trend, volatility, liquidity, GEX/VEX estimates.
  - `OptionsFlowEngine`: filters and scores institutional flow, rejecting lotto trades.
  - `TechnicalEngine`: computes RSI, MACD, EMAs, VWAP bias, and volume trend.
  - `CandidateBuilder`: merges flow with price + context.
  - `ClassificationEngine`: tags structural vs. catalyst-driven patterns.
  - `ScoringEngine`: aggregates weighted signals into a 0–100 confidence with grades.
  - `RoutingEngine`: pushes signals to Immediate Alerts, Intraday Watch, Swing Watch, or Reject and auto-refreshes queues.
- **Learning (`src/learning`)**: tracks performance and nudges scoring weights based on reliability.
- **Alerts (`src/alerts`)**: Webhook transports (Telegram primary, Discord optional) emitting human-readable payloads.
- **Persistence (`src/core/storage.py`)**: SQLite-backed ledger for queued alerts needing later movement validation.
- **Orchestration (`src/core/brain.py`)**: coordinates the end-to-end run for a list of tickers.
- **Scheduler (`src/core/scheduler.py`)**: APScheduler wrapper to refresh watch queues periodically.

## Data Contracts

Key schemas live in `src/models/schemas.py`:
- `MarketRegimeState`, `FlowEvent`, `PriceSnapshot`, `TechnicalContext`, `Candidate`, `ScoreResult`, and `RoutedSignal` define the pipeline inputs/outputs.

## Queues and Promotion

Routing thresholds:
- `>=85` → Immediate Alert
- `65–84` → Intraday Watch (promotes to Immediate if upgraded)
- `50–64` → Swing Watch
- `<50` → Reject

Queues expire automatically (`queues` config) and are refreshed every scheduler tick.

## Extensibility

- Add new data providers by subclassing `BaseProvider` and registering inside `DataService`.
- Inject new transports in `alerts.dispatcher.AlertDispatcher`.
- Add scoring features by extending `ScoringEngine.weights` and helper functions.
