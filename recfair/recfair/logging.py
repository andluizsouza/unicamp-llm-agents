"""Logging setup for CLI and eval runs."""

from __future__ import annotations

import logging


def configure_logging(level: int = logging.WARNING) -> None:
    """Configure root logging and silence noisy third-party loggers."""
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("google_genai.models").setLevel(logging.ERROR)
