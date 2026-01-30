import logging
from pathlib import Path

from src.seedwork.settings import DEBUG

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOG_DIR / "app.log"

_ROOT_LOGGER = logging.getLogger()
_ROOT_LOGGER.setLevel(LOG_LEVEL)

formatter = logging.Formatter(LOG_FORMAT)

console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(formatter)
_ROOT_LOGGER.handlers.clear()
_ROOT_LOGGER.addHandler(console_handler)

file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter)
_ROOT_LOGGER.addHandler(file_handler)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with the global log level."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    return logger
