"""
VendorOS - Utility: Logging
Configures structured logging for the entire application.
Call ``setup_logging()`` once at startup (in ``main.py``).
"""

import logging
import sys
from typing import Optional

from app.core.config import settings

# ANSI colour codes for console output
_COLOURS = {
    "DEBUG": "\033[36m",     # cyan
    "INFO": "\033[32m",      # green
    "WARNING": "\033[33m",   # yellow
    "ERROR": "\033[31m",     # red
    "CRITICAL": "\033[35m",  # magenta
    "RESET": "\033[0m",
}


class ColouredFormatter(logging.Formatter):
    """Logging formatter that injects ANSI colour codes per level."""

    FMT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, _COLOURS["RESET"])
        reset = _COLOURS["RESET"]
        formatter = logging.Formatter(
            f"{colour}{self.FMT}{reset}", datefmt="%Y-%m-%d %H:%M:%S"
        )
        return formatter.format(record)


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure root logger and silence noisy third-party loggers.

    Parameters
    ----------
    level:
        Override log level (e.g. ``"DEBUG"``). Falls back to ``"DEBUG"``
        when ``settings.DEBUG`` is True, otherwise ``"INFO"``.
    """
    log_level = level or ("DEBUG" if settings.DEBUG else "INFO")

    root = logging.getLogger()
    root.setLevel(log_level)

    # Remove existing handlers to avoid duplicate log lines on reload
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColouredFormatter())
    root.addHandler(console_handler)

    # Silence noisy libraries
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "passlib"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("app").setLevel(log_level)

    logging.getLogger(__name__).info(
        "Logging initialised [level=%s, debug=%s]", log_level, settings.DEBUG
    )