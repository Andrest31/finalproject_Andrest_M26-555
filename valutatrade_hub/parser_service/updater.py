"""Обновление и кеширование валютных курсов."""

from datetime import UTC, datetime

from valutatrade_hub.core.exceptions import APIError, RateNotFoundError
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateClient,
)
from valutatrade_hub.parser_service.storage import RateStorage


class RatesUpdater:
    """Получает курсы через API и управляет TTL-кешем."""

    def __init__(self):
        self._storage = RateStorage()
        self._settings = SettingsLoader()
        self._crypto_client = CoinGeckoClient()
        self._fiat_client = ExchangeRateClient()

    def is_cache_fresh(self) -> bool:
        """Проверяет актуальность кеша."""
        cached = self._storage.get_rates()
        timestamp = cached.get("last_refresh")

        if not timestamp or not cached.get("pairs"):
            return False

        try:
            refreshed_at = datetime.fromisoformat(timestamp)

            if refreshed_at.tzinfo is None:
                return False

            age = (datetime.now(UTC) - refreshed_at).total_seconds()
            ttl = self._settings.get("rates_ttl_seconds")

            return 0 <= age < ttl

        except ValueError, TypeError:
            return False

    def update_rates(self, force: bool = False) -> dict[str, float]:
        """Обновляет курсы, если кеш устарел или указан force."""
        cached = self._storage.get_rates()

        if not force and self.is_cache_fresh():
            return cached["pairs"]

        crypto_rates = self._crypto_client.get_rates()
        fiat_rates = self._fiat_client.get_rates()

        rates = {**crypto_rates, **fiat_rates}
        self._storage.save_rates(rates)

        return rates

    def get_rate(self, currency_code: str) -> float:
        """Возвращает курс одной валюты к USD."""
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")

        code = currency_code.strip().upper()

        if code == "USD":
            return 1.0

        try:
            rates = self.update_rates()
        except APIError, RateNotFoundError:
            cached = self._storage.get_rates()

            if not cached.get("pairs"):
                raise

            rates = cached["pairs"]

        pair = f"{code}_USD"

        if pair not in rates:
            raise RateNotFoundError(f"Курс {pair} не найден")

        return rates[pair]

    def get_all_rates(self) -> dict[str, float]:
        """Возвращает все доступные курсы."""
        return self.update_rates()
