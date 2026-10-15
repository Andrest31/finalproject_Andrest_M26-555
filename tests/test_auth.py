"""Тесты регистрации и авторизации."""

from unittest.mock import patch

import pytest

from valutatrade_hub.core.usecases import ValutaTrade


class FakeDatabase:
    """Временное хранилище для тестов."""

    def __init__(self):
        self.users = []
        self.portfolios = []

    def get_users(self):
        return [user.copy() for user in self.users]

    def save_users(self, users):
        self.users = [user.copy() for user in users]

    def get_portfolios(self):
        return [portfolio.copy() for portfolio in self.portfolios]

    def save_portfolios(self, portfolios):
        self.portfolios = [portfolio.copy() for portfolio in portfolios]


@pytest.fixture
def app():
    """Создаёт приложение с изолированным хранилищем."""
    fake_db = FakeDatabase()

    with patch(
        "valutatrade_hub.core.usecases.DatabaseManager",
        return_value=fake_db,
    ):
        application = ValutaTrade()

    return application


def test_register(app):
    """Проверяет регистрацию пользователя."""
    user = app.register("alice", "1234")

    assert user.user_id == 1
    assert user.username == "alice"
    assert len(app._db.get_users()) == 1
    assert len(app._db.get_portfolios()) == 1


def test_register_duplicate_username(app):
    """Запрещает повторную регистрацию имени."""
    app.register("alice", "1234")

    with pytest.raises(ValueError, match="уже занято"):
        app.register("alice", "5678")


def test_login_success(app):
    """Проверяет успешную авторизацию."""
    app.register("alice", "1234")

    user = app.login("alice", "1234")

    assert user.username == "alice"
    assert app.current_user is user


def test_login_wrong_password(app):
    """Проверяет ошибку неправильного пароля."""
    app.register("alice", "1234")

    with pytest.raises(ValueError, match="Неверный пароль"):
        app.login("alice", "wrong")


def test_login_unknown_user(app):
    """Проверяет авторизацию неизвестного пользователя."""
    with pytest.raises(ValueError, match="не найден"):
        app.login("unknown", "1234")


def test_logout(app):
    """Проверяет завершение сессии."""
    app.register("alice", "1234")
    app.login("alice", "1234")

    app.logout()

    assert app.current_user is None
