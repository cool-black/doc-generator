"""Logging configuration."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"doc_gen.{name}")
