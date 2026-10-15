"""Декораторы для логирования операций приложения."""

import logging
import time
from functools import wraps

logger = logging.getLogger("valutatrade_hub")


def log_action(action_name: str):
    """Записывает результат выполнения операции."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info("Начало операции: %s", action_name)

            try:
                result = func(*args, **kwargs)
            except Exception:
                logger.exception("Ошибка операции: %s", action_name)
                raise

            logger.info("Операция выполнена: %s", action_name)
            return result

        return wrapper

    return decorator


def log_time(func):
    """Измеряет время выполнения функции."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()

        try:
            return func(*args, **kwargs)
        finally:
            duration = time.perf_counter() - start
            logger.info(
                "Время выполнения %s: %.4f сек.",
                func.__name__,
                duration,
            )

    return wrapper
