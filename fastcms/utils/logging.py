# fastcms/utils/logging.py

import logging
from typing import Literal

# Cache to prevent re-initialization
_logging_initialized: bool = False

def setup_logging(
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
        log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=True,
        file: str | None = None,
        mode: Literal["w", "a"] = "a",
):
    """Set up logging configuration."""
    global _logging_initialized
    if _logging_initialized:
        return

    # Normalize level to uppercase
    level = level.upper()
    if not hasattr(logging, level):
        raise ValueError(f"Invalid logging level: {level}")
    numeric_level = getattr(logging, level)

    handlers = []
    if stream:
        handlers.append(logging.StreamHandler())

    if file:
        handlers.append(logging.FileHandler(file, mode=mode))

    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers,
    )

    _logging_initialized = True


def get_logger(name: str = "fastcms") -> logging.Logger:
    return logging.getLogger(name)