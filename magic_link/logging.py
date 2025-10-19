"""Logging helpers for the magic_link package."""

from __future__ import annotations

import logging
from typing import Optional

LOGGER_NAME = "magic_link"


def get_logger() -> logging.Logger:
    """Return the shared magic_link logger."""
    return logging.getLogger(LOGGER_NAME)


def configure_logger(level: int = logging.INFO, *, propagate: bool = False) -> logging.Logger:
    """
    Configure a console logger if no handlers are attached.

    Developers can call this during initialization to quickly surface operational logs.
    """
    logger = get_logger()
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | magic_link | %(message)s",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = propagate
    return logger


def enable_debug_logging() -> None:
    """Helper to switch the shared logger into debug mode."""
    configure_logger(level=logging.DEBUG)
