"""Бизнес-логика приложения ValutaTrade Hub."""

import math

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.decorators import log_action, log_time
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.parser_service.updater import RatesUpdater


class ValutaTrade:
    """Управляет пользователями и валютными операциями."""

    def __init__(self):
        self._db = DatabaseManager()
        self._current_user: User | None = None
        self._rates_updater = RatesUpdater()

    @property
    def current_user(self) -> User | None:
        """Возвращает авторизованного пользователя."""
        return self._current_user

    @log_action("Регистрация пользователя")
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

    @log_action("Авторизация пользователя")
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

    def _require_login(self) -> User:
        """Проверяет, что пользователь авторизован."""
        if self._current_user is None:
            raise ValueError("Сначала войдите в систему")
        return self._current_user

    def _load_portfolio(self) -> Portfolio:
        """Загружает портфель текущего пользователя."""
        user = self._require_login()

        for data in self._db.get_portfolios():
            if data["user_id"] == user.user_id:
                return Portfolio.from_dict(user, data)

        raise ValueError("Портфель пользователя не найден")

    def _save_portfolio(self, portfolio: Portfolio) -> None:
        """Сохраняет обновлённый портфель."""
        portfolios = self._db.get_portfolios()

        for index, data in enumerate(portfolios):
            if data["user_id"] == portfolio.user_id:
                portfolios[index] = portfolio.to_dict()
                self._db.save_portfolios(portfolios)
                return

        raise ValueError("Портфель пользователя не найден")

    def show_portfolio(self) -> dict[str, float]:
        """Возвращает балансы всех кошельков."""
        portfolio = self._load_portfolio()

        return {code: wallet.balance for code, wallet in portfolio.wallets.items()}

    def _get_rate(self, currency_code: str) -> float:
        """Возвращает актуальный курс валюты к USD."""
        from valutatrade_hub.core.exceptions import RateNotFoundError

        code = get_currency(currency_code).code

        if code == "USD":
            return 1.0

        # Для торговых операций используем только свежий кеш.
        # Если кеш устарел, запрашиваем новые курсы через API.
        rates = self._rates_updater.update_rates()

        pair = f"{code}_USD"

        if pair not in rates:
            raise RateNotFoundError(f"Курс {pair} не найден")

        rate = rates[pair]

        if (
            isinstance(rate, bool)
            or not isinstance(rate, (int, float))
            or not 0 < rate < float("inf")
        ):
            raise ValueError(f"Некорректный курс {pair}")

        return float(rate)

    @staticmethod
    def _validate_amount(amount: float) -> None:
        """Проверяет сумму операции."""
        if (
            isinstance(amount, bool)
            or not isinstance(amount, (int, float))
            or not 0 < amount < float("inf")
        ):
            raise ValueError("Сумма должна быть положительным конечным числом")

    @log_action("Покупка валюты")
    @log_time
    def buy(self, currency_code: str, amount: float) -> float:
        """Покупает валюту за USD."""
        self._validate_amount(amount)

        currency = get_currency(currency_code)
        code = currency.code

        if code == "USD":
            raise ValueError("Нельзя купить USD за USD")

        portfolio = self._load_portfolio()
        rate = self._get_rate(code)
        cost = amount * rate

        if not math.isfinite(cost):
            raise ValueError("Слишком большая сумма покупки")

        usd_wallet = portfolio.get_wallet("USD")
        if usd_wallet is None:
            raise ValueError("У пользователя отсутствует USD-кошелёк")

        # Сначала проверяем возможность списания.
        if usd_wallet.balance < cost:
            raise ValueError(
                f"Недостаточно USD: доступно {usd_wallet.balance:.2f}, "
                f"требуется {cost:.2f}"
            )

        currency_wallet = portfolio.add_currency(code)

        usd_wallet.withdraw(cost)
        currency_wallet.deposit(amount)

        self._save_portfolio(portfolio)
        return cost

    @log_action("Продажа валюты")
    @log_time
    def sell(self, currency_code: str, amount: float) -> float:
        """Продаёт валюту и начисляет USD."""
        self._validate_amount(amount)

        currency = get_currency(currency_code)
        code = currency.code

        if code == "USD":
            raise ValueError("Нельзя продать USD за USD")

        portfolio = self._load_portfolio()
        rate = self._get_rate(code)
        revenue = amount * rate

        if not math.isfinite(revenue):
            raise ValueError("Слишком большая сумма продажи")

        currency_wallet = portfolio.get_wallet(code)
        if currency_wallet is None:
            raise ValueError(f"Кошелёк {code} отсутствует")

        usd_wallet = portfolio.add_currency("USD")

        currency_wallet.withdraw(amount)
        usd_wallet.deposit(revenue)

        self._save_portfolio(portfolio)
        return revenue

    def deposit_usd(self, amount: float) -> None:
        """Пополняет виртуальный USD-баланс для демонстрации."""
        self._validate_amount(amount)

        portfolio = self._load_portfolio()
        portfolio.add_currency("USD").deposit(amount)
        self._save_portfolio(portfolio)
