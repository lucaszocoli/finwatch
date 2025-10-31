import logging
import os
from pathlib import Path


def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/finwatch.log", encoding="utf-8"),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"finwatch.{name}")
