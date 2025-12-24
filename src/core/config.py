from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised when dependency missing
    yaml = None


class ConfigError(Exception):
    pass


@lru_cache(maxsize=1)
def load_config(path: str | Path = "config/settings.yaml") -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        fallback = config_path.with_name(f"{config_path.stem}.example{config_path.suffix}")
        if fallback.exists():
            config_path = fallback
        else:
            raise ConfigError(f"Config file not found at {config_path}")
    raw_text = config_path.read_text()
    if yaml:
        raw = yaml.safe_load(raw_text) or {}
    else:
        raw = _fallback_yaml_parse(raw_text)
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


def _fallback_yaml_parse(text: str) -> Dict[str, Any]:
    """Very small YAML subset parser for nested mappings.

    Supports keys/values separated by a colon and indentation-based nesting.
    Booleans, ints, floats, and strings are handled; lists are not supported.
    """

    def cast(value: str) -> Any:
        lower = value.lower()
        if lower == "true":
            return True
        if lower == "false":
            return False
        if lower == "null":
            return None
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    root: Dict[str, Any] = {}
    stack: list[tuple[int, Dict[str, Any]]] = [(0, root)]

    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, remainder = line.lstrip().partition(":")
        if not _:
            continue
        value = remainder.strip()
        while stack and indent < stack[-1][0]:
            stack.pop()
        current = stack[-1][1]
        if value == "":
            new_dict: Dict[str, Any] = {}
            current[key] = new_dict
            stack.append((indent + 1, new_dict))
        else:
            current[key] = cast(value)
    return root
