"""Тесты покупки, продажи и обработки ошибок курсов."""

from copy import deepcopy
from unittest.mock import patch

import pytest

from valutatrade_hub.core.exceptions import APIError
from valutatrade_hub.core.usecases import ValutaTrade


class FakeDatabase:
    """Изолированное хранилище для тестов."""

    def __init__(self):
        self.users = []
        self.portfolios = []

    def get_users(self):
        return deepcopy(self.users)

    def save_users(self, users):
        self.users = deepcopy(users)

    def get_portfolios(self):
        return deepcopy(self.portfolios)

    def save_portfolios(self, portfolios):
        self.portfolios = deepcopy(portfolios)


@pytest.fixture
def app():
    """Создаёт авторизованное приложение с тестовым балансом."""
    fake_db = FakeDatabase()

    with patch(
        "valutatrade_hub.core.usecases.DatabaseManager",
        return_value=fake_db,
    ):
        application = ValutaTrade()

    application.register("trader", "1234")
    application.login("trader", "1234")
    application.deposit_usd(10000)

    # Подменяем курсы, чтобы тесты не обращались к API.
    application._rates_updater.update_rates = lambda: {
        "BTC_USD": 60000.0,
        "ETH_USD": 3000.0,
        "EUR_USD": 1.1,
    }

    return application


def test_buy_success(app):
    """Покупка списывает USD и начисляет BTC."""
    cost = app.buy("BTC", 0.1)
    balances = app.show_portfolio()

    assert cost == pytest.approx(6000)
    assert balances["USD"] == pytest.approx(4000)
    assert balances["BTC"] == pytest.approx(0.1)


def test_sell_success(app):
    """Продажа BTC начисляет USD."""
    app.buy("BTC", 0.1)

    revenue = app.sell("BTC", 0.05)
    balances = app.show_portfolio()

    assert revenue == pytest.approx(3000)
    assert balances["USD"] == pytest.approx(7000)
    assert balances["BTC"] == pytest.approx(0.05)


def test_buy_insufficient_usd(app):
    """Нельзя купить валюту без достаточного количества USD."""
    before = app.show_portfolio()

    with pytest.raises(ValueError, match="Недостаточно USD"):
        app.buy("BTC", 1)

    assert app.show_portfolio() == before


def test_sell_insufficient_currency(app):
    """Нельзя продать больше валюты, чем имеется."""
    app.buy("BTC", 0.01)
    before = app.show_portfolio()

    with pytest.raises(Exception, match="Недостаточно средств"):
        app.sell("BTC", 1)

    assert app.show_portfolio() == before


@pytest.mark.parametrize("amount", [0, -1, float("nan"), float("inf")])
def test_buy_invalid_amount(app, amount):
    """Некорректная сумма покупки не изменяет баланс."""
    before = app.show_portfolio()

    with pytest.raises(ValueError):
        app.buy("BTC", amount)

    assert app.show_portfolio() == before


def test_buy_unknown_currency(app):
    """Неизвестную валюту нельзя купить."""
    before = app.show_portfolio()

    with pytest.raises(Exception, match="не поддерживается"):
        app.buy("ABC", 1)

    assert app.show_portfolio() == before


def test_api_failure_does_not_change_balance(app):
    """Сбой API не должен приводить к списанию средств."""
    before = app.show_portfolio()

    with patch.object(
        app._rates_updater,
        "update_rates",
        side_effect=APIError("API недоступен"),
    ):
        with pytest.raises(APIError):
            app.buy("BTC", 0.01)

    assert app.show_portfolio() == before


def test_sell_api_failure_does_not_change_balance(app):
    """При сбое API продажа не должна изменять баланс."""
    app.buy("BTC", 0.1)
    before = app.show_portfolio()

    with patch.object(
        app._rates_updater,
        "update_rates",
        side_effect=APIError("API недоступен"),
    ):
        with pytest.raises(APIError):
            app.sell("BTC", 0.05)

    assert app.show_portfolio() == before


def test_trade_persists_in_database(app):
    """Результат сделки сохраняется в хранилище."""
    app.buy("BTC", 0.1)

    saved = app._db.get_portfolios()[0]["wallets"]

    assert saved["USD"]["balance"] == pytest.approx(4000)
    assert saved["BTC"]["balance"] == pytest.approx(0.1)


def test_trade_requires_login(app):
    """Торговля запрещена без авторизации."""
    app.logout()

    with pytest.raises(ValueError, match="Сначала войдите"):
        app.buy("BTC", 0.01)
