"""Модели валют и фабрика валютных объектов."""

from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс валюты."""

    def __init__(self, code: str, name: str):
        self._code = code.upper()
        self._name = name

    @property
    def code(self) -> str:
        """Возвращает код валюты."""
        return self._code

    @property
    def name(self) -> str:
        """Возвращает название валюты."""
        return self._name

    @abstractmethod
    def get_info(self) -> str:
        """Возвращает описание валюты."""


class FiatCurrency(Currency):
    """Обычная государственная валюта."""

    def __init__(self, code: str, name: str, country: str):
        super().__init__(code, name)
        self._country = country

    @property
    def country(self) -> str:
        """Возвращает страну или регион валюты."""
        return self._country

    def get_info(self) -> str:
        """Возвращает информацию о фиатной валюте."""
        return f"{self.code} — {self.name} (фиатная валюта, {self.country})"


class CryptoCurrency(Currency):
    """Криптовалюта."""

    def __init__(
        self,
        code: str,
        name: str,
        blockchain: str,
    ):
        super().__init__(code, name)
        self._blockchain = blockchain

    @property
    def blockchain(self) -> str:
        """Возвращает название блокчейна."""
        return self._blockchain

    def get_info(self) -> str:
        """Возвращает информацию о криптовалюте."""
        return f"{self.code} — {self.name} (криптовалюта, блокчейн: {self.blockchain})"


CURRENCY_REGISTRY: dict[str, Currency] = {
    "USD": FiatCurrency("USD", "US Dollar", "США"),
    "EUR": FiatCurrency("EUR", "Euro", "Еврозона"),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Россия"),
    "GBP": FiatCurrency("GBP", "Pound Sterling", "Великобритания"),
    "JPY": FiatCurrency("JPY", "Japanese Yen", "Япония"),
    "BTC": CryptoCurrency("BTC", "Bitcoin", "Bitcoin"),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethereum"),
    "SOL": CryptoCurrency("SOL", "Solana", "Solana"),
    "ADA": CryptoCurrency("ADA", "Cardano", "Cardano"),
    "DOGE": CryptoCurrency("DOGE", "Dogecoin", "Dogecoin"),
}


def get_currency(code: str) -> Currency:
    """Возвращает валюту из реестра по её коду."""
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Код валюты не может быть пустым")

    normalized_code = code.strip().upper()

    try:
        return CURRENCY_REGISTRY[normalized_code]
    except KeyError as error:
        raise CurrencyNotFoundError(normalized_code) from error
