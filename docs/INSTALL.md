# Installation Guide

1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies: `pip install -e .`
3. Copy `config/settings.example.yaml` to `config/settings.yaml` and update values.
4. Copy `.env.example` to `.env` and provide API keys (and optional `ALERT_DB_PATH`). Ensure the parent directory for the database exists.
5. Run tests with `pytest`.
6. Start the scheduler: `python scripts/run_brain.py`
