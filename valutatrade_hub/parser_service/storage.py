"""Хранение актуальных курсов и истории обновлений."""

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader


class RateStorage:
    """Управляет кешем и историей валютных курсов."""

    def __init__(self):
        self._db = DatabaseManager()
        self._settings = SettingsLoader()

        data_dir = self._settings.get_path("data_dir")
        history_file = self._settings.get("history_file")

        self._history_path = data_dir / history_file
        self._history_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._history_path.exists():
            self._write_history([])

    def get_rates(self) -> dict:
        """Возвращает текущий кеш курсов."""
        return self._db.get_rates()

    def save_rates(self, rates: dict[str, float]) -> None:
        """Сохраняет курсы и время обновления."""
        timestamp = datetime.now(UTC).isoformat()

        self._db.save_rates(
            {
                "pairs": rates,
                "last_refresh": timestamp,
            }
        )

        history = self.get_history()
        history.append(
            {
                "timestamp": timestamp,
                "pairs": rates,
            }
        )
        self._write_history(history)

    def get_history(self) -> list[dict]:
        """Читает историю обновлений."""
        with self._history_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_history(self, history: list[dict]) -> None:
        """Атомарно сохраняет историю обновлений."""
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._history_path.parent,
                prefix=".exchange_rates_",
                suffix=".tmp",
                delete=False,
            ) as file:
                temp_path = Path(file.name)
                json.dump(history, file, ensure_ascii=False, indent=4)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_path, self._history_path)

        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
