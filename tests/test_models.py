"""Тесты моделей пользователя, кошелька и портфеля."""

import pytest

from valutatrade_hub.core.exceptions import (
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.models import Portfolio, User, Wallet


def test_user_password():
    """Проверяет правильный и неправильный пароль."""
    user = User(1, "alice", password="1234")

    assert user.verify_password("1234")
    assert not user.verify_password("wrong")
    assert user.username == "alice"


def test_user_serialization():
    """Проверяет восстановление пользователя из JSON-данных."""
    user = User(1, "alice", password="1234")
    restored = User.from_dict(user.to_dict())

    assert restored.user_id == user.user_id
    assert restored.username == user.username
    assert restored.verify_password("1234")


def test_user_empty_username():
    """Запрещает пустое имя пользователя."""
    with pytest.raises(ValueError):
        User(1, "   ", password="1234")


def test_wallet_deposit_and_withdraw():
    """Проверяет пополнение и списание."""
    wallet = Wallet("BTC")

    wallet.deposit(0.5)
    wallet.withdraw(0.2)

    assert wallet.balance == pytest.approx(0.3)


def test_wallet_insufficient_funds():
    """Запрещает списание сверх баланса."""
    wallet = Wallet("USD", balance=100)

    with pytest.raises(InsufficientFundsError):
        wallet.withdraw(150)

    assert wallet.balance == 100


@pytest.mark.parametrize("amount", [0, -10, float("nan"), float("inf")])
def test_wallet_invalid_amount(amount):
    """Запрещает некорректные суммы."""
    wallet = Wallet("USD")

    with pytest.raises(ValueError):
        wallet.deposit(amount)


def test_wallet_serialization():
    """Проверяет восстановление кошелька."""
    wallet = Wallet("EUR", balance=250)
    restored = Wallet.from_dict(wallet.to_dict())

    assert restored.currency_code == "EUR"
    assert restored.balance == 250


def test_portfolio_add_currency():
    """Проверяет добавление кошелька без дубликатов."""
    user = User(1, "alice", password="1234")
    portfolio = Portfolio(user)

    first = portfolio.add_currency("BTC")
    second = portfolio.add_currency("btc")

    assert first is second
    assert len(portfolio.wallets) == 1


def test_portfolio_unknown_currency():
    """Запрещает добавление неизвестной валюты."""
    user = User(1, "alice", password="1234")
    portfolio = Portfolio(user)

    with pytest.raises(CurrencyNotFoundError):
        portfolio.add_currency("ABC")


def test_portfolio_total_value():
    """Проверяет стоимость портфеля в USD."""
    user = User(1, "alice", password="1234")
    portfolio = Portfolio(user)

    portfolio.add_currency("USD").deposit(1000)
    portfolio.add_currency("BTC").deposit(0.1)

    rates = {"BTC_USD": 60000}

    assert portfolio.get_total_value("USD", rates) == pytest.approx(7000)


def test_portfolio_serialization():
    """Проверяет восстановление портфеля."""
    user = User(1, "alice", password="1234")
    portfolio = Portfolio(user)
    portfolio.add_currency("BTC").deposit(0.5)

    restored = Portfolio.from_dict(user, portfolio.to_dict())

    assert restored.user_id == user.user_id
    assert restored.get_wallet("BTC").balance == 0.5
