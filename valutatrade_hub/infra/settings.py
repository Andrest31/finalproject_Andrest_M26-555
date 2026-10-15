"""Загрузка и хранение настроек приложения."""

import tomllib
from pathlib import Path
from threading import Lock
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SettingsLoader:
    """Singleton для централизованного доступа к конфигурации."""

    _instance = None
    _lock = Lock()

    DEFAULT_SETTINGS = {
        "data_dir": "data",
        "users_file": "users.json",
        "portfolios_file": "portfolios.json",
        "rates_file": "rates.json",
        "history_file": "exchange_rates.json",
        "rates_ttl_seconds": 300,
        "base_currency": "USD",
        "log_dir": "logs",
        "log_file": "actions.log",
        "log_level": "INFO",
        "log_format": "text",
        "log_max_bytes": 1_048_576,
        "log_backup_count": 3,
    }

    def __new__(cls):
        """Гарантирует создание единственного экземпляра."""
        with cls._lock:
            if cls._instance is None:
                # __new__ выбран из-за простоты и читаемости.
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Загружает конфигурацию при первой инициализации."""
        if self._initialized:
            return

        self._config_path = PROJECT_ROOT / "pyproject.toml"
        self._settings: dict[str, Any] = {}
        self.reload()
        self._initialized = True

    def reload(self) -> None:
        """Повторно загружает настройки из pyproject.toml."""
        settings = self.DEFAULT_SETTINGS.copy()

        if self._config_path.exists():
            with self._config_path.open("rb") as file:
                config = tomllib.load(file)

            custom_settings = config.get("tool", {}).get("valutatrade", {})
            settings.update(custom_settings)

        self._settings = settings

    def get(self, key: str, default: Any = None) -> Any:
        """Возвращает значение настройки или default."""
        return self._settings.get(key, default)

    def get_path(self, key: str) -> Path:
        """Возвращает абсолютный путь к файлу или каталогу."""
        value = self.get(key)

        if not isinstance(value, str):
            raise ValueError(f"Настройка '{key}' должна быть строкой")

        path = Path(value)

        if not path.is_absolute():
            path = PROJECT_ROOT / path

        return path
