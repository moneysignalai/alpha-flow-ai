# Alpha Flow AI

Super-intelligent AI trading brain that detects institutional options flow and routes actionable alerts.

## Features
- Institutional options flow detection with conviction scoring
- Market regime and gamma/VEX assessment
- Technical enrichment (RSI, MACD, EMAs, VWAP, volume trend)
- Classification + scoring engine with route thresholds
- Auto-refreshing queues for immediate, intraday, swing decisions
- Telegram alerts (Discord/webhook extensible)
- Learning engine that adapts weights by reliability
- Scheduler for continuous monitoring

## Repository Layout
```
/src
  /core           # config, logging, orchestration, scheduler
  /engines        # regime, options flow, technicals, scoring, routing
  /data           # data providers and caching
  /models         # dataclasses / schemas
  /alerts         # alert transports
  /learning       # adaptive weighting and analytics
/config           # configuration templates
/docs             # architecture and install docs
/tests            # unit and simulation tests
/scripts          # operational scripts
```

## Quickstart
1. Create virtualenv and install dependencies: `pip install -e .`
2. Copy `.env.example` to `.env` and supply API keys.
3. Copy `config/settings.example.yaml` to `config/settings.yaml` and tune values.
4. Run tests with `pytest`.
5. Start the scheduler: `python scripts/run_brain.py`

## Configuration
- `config/settings.example.yaml` documents application, data, alert, queue, and learning settings.
- Environment variables resolve secrets (Massive/Polygon market data, Benzinga, Telegram, Discord).

## Docs
See `/docs/ARCHITECTURE.md` for deep architecture notes and `/docs/INSTALL.md` for setup.
