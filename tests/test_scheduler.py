"""Тесты фонового планировщика курсов."""

import threading
from unittest.mock import Mock

import pytest

from valutatrade_hub.parser_service.scheduler import RatesScheduler


def test_invalid_interval():
    """Нельзя установить нулевой или отрицательный интервал."""
    with pytest.raises(ValueError):
        RatesScheduler(interval_seconds=0)

    with pytest.raises(ValueError):
        RatesScheduler(interval_seconds=-10)


def test_scheduler_start_and_stop():
    """Планировщик запускается и корректно останавливается."""
    scheduler = RatesScheduler(interval_seconds=60)
    updated = threading.Event()

    def fake_update(force=False):
        updated.set()
        return {"BTC_USD": 60000.0}

    scheduler.updater.update_rates = fake_update

    scheduler.start()

    try:
        assert updated.wait(timeout=3)
        assert scheduler._thread.is_alive()
    finally:
        scheduler.stop()

    assert scheduler._thread is None


def test_scheduler_does_not_start_twice():
    """Повторный запуск не создаёт второй поток."""
    scheduler = RatesScheduler(interval_seconds=60)
    scheduler.updater.update_rates = Mock(return_value={})

    scheduler.start()

    try:
        first_thread = scheduler._thread
        scheduler.start()

        assert scheduler._thread is first_thread
    finally:
        scheduler.stop()


def test_scheduler_handles_api_error():
    """Ошибка обновления не завершает фоновый поток."""
    scheduler = RatesScheduler(interval_seconds=60)
    attempted = threading.Event()

    def fake_update(force=False):
        attempted.set()
        raise RuntimeError("API недоступен")

    scheduler.updater.update_rates = fake_update

    scheduler.start()

    try:
        assert attempted.wait(timeout=3)
        assert scheduler._thread.is_alive()
    finally:
        scheduler.stop()
