"""Управление JSON-хранилищем приложения."""

import json
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any


class DatabaseManager:
    """Единый менеджер для чтения и записи JSON-файлов."""

    _instance = None
    _instance_lock = RLock()

    def __new__(cls):
        """Создаёт только один экземпляр менеджера."""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str | Path | None = None):
        """Настраивает пути к JSON-хранилищу."""
        if self._initialized:
            return

        self._lock = RLock()

        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[2] / "data"

        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

        self._users_path = self._data_dir / "users.json"
        self._portfolios_path = self._data_dir / "portfolios.json"
        self._rates_path = self._data_dir / "rates.json"

        self._ensure_file(self._users_path, [])
        self._ensure_file(self._portfolios_path, [])
        self._ensure_file(
            self._rates_path,
            {"pairs": {}, "last_refresh": None},
        )

        self._initialized = True

    @staticmethod
    def _ensure_file(path: Path, default: Any) -> None:
        """Создаёт JSON-файл, если он отсутствует."""
        if not path.exists():
            path.write_text(
                json.dumps(default, ensure_ascii=False, indent=4),
                encoding="utf-8",
            )

    def _read_json(self, path: Path) -> Any:
        """Читает JSON-файл."""
        with self._lock:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)

    def _write_json(self, path: Path, data: Any) -> None:
        """Атомарно записывает JSON через временный файл."""
        with self._lock:
            temp_path = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=path.parent,
                    prefix=f".{path.stem}_",
                    suffix=".tmp",
                    delete=False,
                ) as file:
                    temp_path = Path(file.name)
                    json.dump(data, file, ensure_ascii=False, indent=4)
                    file.flush()
                    os.fsync(file.fileno())

                os.replace(temp_path, path)

            finally:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)

    def get_users(self) -> list[dict]:
        """Возвращает список пользователей."""
        return self._read_json(self._users_path)

    def save_users(self, users: list[dict]) -> None:
        """Сохраняет список пользователей."""
        self._write_json(self._users_path, users)

    def get_portfolios(self) -> list[dict]:
        """Возвращает список портфелей."""
        return self._read_json(self._portfolios_path)

    def save_portfolios(self, portfolios: list[dict]) -> None:
        """Сохраняет список портфелей."""
        self._write_json(self._portfolios_path, portfolios)

    def get_rates(self) -> dict:
        """Возвращает кеш валютных курсов."""
        return self._read_json(self._rates_path)

    def save_rates(self, rates: dict) -> None:
        """Сохраняет кеш валютных курсов."""
        self._write_json(self._rates_path, rates)
