"""
CVlect AI — Utility functions
"""

import logging
import os
from datetime import datetime, timezone


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger that avoids leaking sensitive data."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if os.getenv("DEBUG", "true").lower() == "true" else logging.INFO)
    return logger


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def safe_filename(filename: str) -> str:
    """Sanitise a filename to prevent path traversal."""
    import re
    name = os.path.basename(filename)
    name = re.sub(r'[^\w\s\-.]', '', name)
    return name or "unnamed"
