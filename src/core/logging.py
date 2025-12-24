from __future__ import annotations

import logging
from logging import Logger
from typing import Optional


_DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(name: str, level: str = "INFO", fmt: str = _DEFAULT_FORMAT) -> Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


class StructuredAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.pop("extra", {})
        if extra:
            parts = [f"{key}={value}" for key, value in extra.items()]
            msg = f"{msg} | {' '.join(parts)}"
        return msg, kwargs
