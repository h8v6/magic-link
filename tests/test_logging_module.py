import logging

from magic_link.logging import configure_logger, enable_debug_logging, get_logger


def test_configure_logger_creates_handler():
    logger = configure_logger(level=logging.INFO, propagate=False)
    assert logger.level == logging.INFO
    assert not logger.propagate
    assert logger.handlers


def test_enable_debug_logging_sets_level():
    enable_debug_logging()
    logger = get_logger()
    assert logger.level == logging.DEBUG
