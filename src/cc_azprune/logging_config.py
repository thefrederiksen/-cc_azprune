"""Logging configuration for cc_azprune."""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: Path | None = None) -> logging.Logger:
    """Set up logging to both file and console.

    Args:
        log_dir: Directory for log files. Defaults to app directory.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("cc_azprune")

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Determine log file path
    if log_dir is None:
        # Use app directory
        log_dir = Path(__file__).parent.parent.parent / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"cc_azprune_{date_str}.log"

    # File handler - detailed logging
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)

    # Console handler - info and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("=" * 60)
    logger.info("cc_azprune started")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)

    return logger


def get_logger(name: str = "cc_azprune") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (will be prefixed with cc_azprune.)

    Returns:
        Logger instance
    """
    if name == "cc_azprune":
        return logging.getLogger(name)
    return logging.getLogger(f"cc_azprune.{name}")
