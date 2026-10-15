"""Фоновое обновление валютных курсов."""

import logging
import threading

from valutatrade_hub.parser_service.updater import RatesUpdater

logger = logging.getLogger("valutatrade_hub")


class RatesScheduler:
    """Периодически обновляет курсы валют в отдельном потоке."""

    def __init__(self, interval_seconds: int = 300):
        if interval_seconds <= 0:
            raise ValueError("Интервал обновления должен быть положительным")

        self.interval_seconds = interval_seconds
        self.updater = RatesUpdater()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def _run(self) -> None:
        """Цикл обновления курсов."""
        while not self._stop_event.is_set():
            try:
                rates = self.updater.update_rates(force=True)
                logger.info(
                    "Фоновое обновление курсов выполнено: %s пар",
                    len(rates),
                )
            except Exception:
                logger.exception("Ошибка фонового обновления курсов")

            if self._stop_event.wait(self.interval_seconds):
                break

    def start(self) -> None:
        """Запускает планировщик."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="rates-scheduler",
            daemon=True,
        )
        self._thread.start()
        logger.info("Планировщик курсов запущен")

    def stop(self) -> None:
        """Останавливает планировщик."""
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=10)

            if self._thread.is_alive():
                logger.warning("Планировщик не успел завершиться")
            else:
                self._thread = None
                logger.info("Планировщик курсов остановлен")
