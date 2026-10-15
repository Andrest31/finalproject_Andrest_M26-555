"""Бизнес-логика приложения ValutaTrade Hub."""

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.infra.database import DatabaseManager


class ValutaTrade:
    """Управляет пользователями и валютными операциями."""

    def __init__(self):
        self._db = DatabaseManager()
        self._current_user: User | None = None

    @property
    def current_user(self) -> User | None:
        """Возвращает авторизованного пользователя."""
        return self._current_user

    def register(self, username: str, password: str) -> User:
        """Регистрирует нового пользователя."""
        if not isinstance(username, str) or not username.strip():
            raise ValueError("Имя пользователя не может быть пустым")

        users = self._db.get_users()
        username = username.strip()

        if any(user["username"] == username for user in users):
            raise ValueError(f"Имя пользователя '{username}' уже занято")

        user_id = (
            max(
                (user["user_id"] for user in users),
                default=0,
            )
            + 1
        )

        user = User(
            user_id=user_id,
            username=username,
            password=password,
        )

        portfolio = Portfolio(user)

        users.append(user.to_dict())
        self._db.save_users(users)

        portfolios = self._db.get_portfolios()
        portfolios.append(portfolio.to_dict())
        self._db.save_portfolios(portfolios)

        return user

    def login(self, username: str, password: str) -> User:
        """Авторизует пользователя по имени и паролю."""
        users = self._db.get_users()

        for user_data in users:
            if user_data["username"] == username:
                user = User.from_dict(user_data)

                if not user.verify_password(password):
                    raise ValueError("Неверный пароль")

                self._current_user = user
                return user

        raise ValueError(f"Пользователь '{username}' не найден")

    def logout(self) -> None:
        """Завершает текущую сессию."""
        self._current_user = None
