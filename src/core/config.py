from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigError(Exception):
    pass


@lru_cache(maxsize=1)
def load_config(path: str | Path = "config/settings.yaml") -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found at {config_path}")
    raw = yaml.safe_load(config_path.read_text()) or {}
    return _resolve_env(raw)


def _resolve_env(config: Dict[str, Any]) -> Dict[str, Any]:
    resolved: Dict[str, Any] = {}
    for key, value in config.items():
        if isinstance(value, dict):
            resolved[key] = _resolve_env(value)
        elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_key = value[2:-1]
            resolved[key] = os.getenv(env_key, "")
        else:
            resolved[key] = value
    return resolved
