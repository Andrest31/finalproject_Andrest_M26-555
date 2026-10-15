"""Настройка логирования приложения."""

import logging
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging() -> logging.Logger:
    """Настраивает логирование в файл с ротацией."""
    settings = SettingsLoader()

    log_dir = settings.get_path("log_dir")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / settings.get("log_file")

    logger = logging.getLogger("valutatrade_hub")
    logger.setLevel(settings.get("log_level", "INFO"))

    if logger.handlers:
        return logger

    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=settings.get("log_max_bytes", 1_048_576),
        backupCount=settings.get("log_backup_count", 3),
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger
