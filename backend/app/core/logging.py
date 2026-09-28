import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "INFO") -> None:
    """Configure standard logging format and root log level."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    )

    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Set third-party loggers to reasonable levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger instance with the given name or root logger."""
    return logging.getLogger(name or "app")
