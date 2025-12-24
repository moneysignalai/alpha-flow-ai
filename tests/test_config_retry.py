import asyncio

from core.config import load_config
from data.providers import with_retry


def test_with_retry_recreates_coroutine():
    call_count = {"n": 0}

    async def flaky():
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("transient")
        return "ok"

    result = asyncio.run(with_retry(flaky, attempts=3, base_delay=0))

    assert result == "ok"
    assert call_count["n"] == 2


def test_load_config_falls_back_to_example(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    example = config_dir / "settings.example.yaml"
    example.write_text("api_key: ${API_KEY}")

    monkeypatch.setenv("API_KEY", "abc123")
    load_config.cache_clear()

    config = load_config(config_dir / "settings.yaml")

    assert config["api_key"] == "abc123"
    load_config.cache_clear()
