"""Клиенты для получения валютных курсов из внешних API."""

import requests

from valutatrade_hub.core.exceptions import APIError, RateNotFoundError


class CoinGeckoClient:
    """Получает курсы криптовалют к USD через CoinGecko."""

    BASE_URL = "https://api.coingecko.com/api/v3/simple/price"

    COIN_IDS = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "ADA": "cardano",
        "DOGE": "dogecoin",
    }

    def get_rates(self) -> dict[str, float]:
        """Возвращает курсы поддерживаемых криптовалют."""
        try:
            response = requests.get(
                self.BASE_URL,
                params={
                    "ids": ",".join(self.COIN_IDS.values()),
                    "vs_currencies": "usd",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

        except (requests.RequestException, ValueError) as error:
            raise APIError(f"Не удалось получить курсы CoinGecko: {error}") from error

        rates = {}

        for code, coin_id in self.COIN_IDS.items():
            try:
                rate = float(data[coin_id]["usd"])
            except (KeyError, TypeError, ValueError) as error:
                raise RateNotFoundError(
                    f"CoinGecko не вернул курс {code}/USD"
                ) from error

            if not 0 < rate < float("inf"):
                raise APIError(f"Некорректный курс {code}/USD")

            rates[f"{code}_USD"] = rate

        return rates


class ExchangeRateClient:
    """Получает курсы фиатных валют через ExchangeRate-API."""

    BASE_URL = "https://open.er-api.com/v6/latest/USD"

    FIAT_CODES = ("EUR", "RUB", "GBP", "JPY")

    def get_rates(self) -> dict[str, float]:
        """Возвращает стоимость фиатных валют в USD."""
        try:
            response = requests.get(
                self.BASE_URL,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

        except (requests.RequestException, ValueError) as error:
            raise APIError(
                f"Не удалось получить курсы ExchangeRate-API: {error}"
            ) from error

        if data.get("result") != "success":
            raise APIError("ExchangeRate-API вернул ошибку")

        conversion_rates = data.get("rates", {})
        rates = {"USD_USD": 1.0}

        for code in self.FIAT_CODES:
            try:
                usd_to_currency = float(conversion_rates[code])
            except (KeyError, TypeError, ValueError) as error:
                raise RateNotFoundError(
                    f"ExchangeRate-API не вернул курс USD/{code}"
                ) from error

            if not 0 < usd_to_currency < float("inf"):
                raise APIError(f"Некорректный курс USD/{code}")

            # API возвращает количество единиц валюты за 1 USD.
            # Для покупки за USD нужна обратная величина.
            rates[f"{code}_USD"] = 1 / usd_to_currency

        return rates
