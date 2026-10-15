"""Консольный интерфейс ValutaTrade Hub."""

import shlex

from valutatrade_hub.core.exceptions import (
    APIError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    RateNotFoundError,
)
from valutatrade_hub.core.usecases import ValutaTrade
from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.parser_service.scheduler import RatesScheduler
from valutatrade_hub.parser_service.updater import RatesUpdater


def parse_arguments(args: list[str]) -> dict[str, str]:
    """Преобразует CLI-аргументы в словарь."""
    if len(args) % 2 != 0:
        raise ValueError("Аргументы должны передаваться парами: --ключ значение")

    parsed = {}

    for index in range(0, len(args), 2):
        key = args[index]
        value = args[index + 1]

        if not key.startswith("--"):
            raise ValueError(f"Некорректный аргумент: {key}")

        key = key[2:]

        if key in parsed:
            raise ValueError(f"Аргумент --{key} указан повторно")

        parsed[key] = value

    return parsed


def require_arguments(
    arguments: dict[str, str],
    required: tuple[str, ...],
) -> None:
    """Проверяет наличие обязательных аргументов."""
    for key in required:
        if key not in arguments:
            raise ValueError(f"Не указан обязательный аргумент --{key}")


def main() -> None:
    """Запускает интерактивный CLI."""
    setup_logging()

    app = ValutaTrade()
    updater = RatesUpdater()
    scheduler = RatesScheduler(interval_seconds=300)

    scheduler.start()

    print("ValutaTrade Hub")
    print("Введите help для списка команд.")

    try:
        while True:
            try:
                command_line = input("\n> ").strip()

                if not command_line:
                    continue

                parts = shlex.split(command_line)
                command = parts[0].lower()
                args = parse_arguments(parts[1:])

                if command == "exit":
                    print("До свидания!")
                    break

                if command == "help":
                    print("Доступные команды:")
                    print("  register --username NAME --password PASSWORD")
                    print("  login --username NAME --password PASSWORD")
                    print("  deposit --amount AMOUNT")
                    print("  show-portfolio")
                    print("  buy --currency CODE --amount AMOUNT")
                    print("  sell --currency CODE --amount AMOUNT")
                    print("  update-rates")
                    print("  get-rate --currency CODE")
                    print("  show-rates")
                    print("  logout")
                    print("  help")
                    print("  exit")

                elif command == "register":
                    require_arguments(args, ("username", "password"))

                    user = app.register(
                        username=args["username"],
                        password=args["password"],
                    )

                    print(
                        f"Пользователь '{user.username}' "
                        f"зарегистрирован (id={user.user_id})."
                    )

                elif command == "login":
                    require_arguments(args, ("username", "password"))

                    user = app.login(
                        username=args["username"],
                        password=args["password"],
                    )

                    print(f"Вы вошли как '{user.username}'")

                elif command == "logout":
                    app.logout()
                    print("Вы вышли из системы")

                elif command == "deposit":
                    require_arguments(args, ("amount",))
                    amount = float(args["amount"])

                    app.deposit_usd(amount)
                    print(f"Баланс пополнен на {amount:.2f} USD")

                elif command == "show-portfolio":
                    balances = app.show_portfolio()

                    if not balances:
                        print("Портфель пуст")
                    else:
                        print("Ваш портфель:")
                        for code, balance in balances.items():
                            print(f"  {code}: {balance:.4f}")

                elif command == "buy":
                    require_arguments(args, ("currency", "amount"))

                    code = args["currency"].upper()
                    amount = float(args["amount"])
                    cost = app.buy(code, amount)

                    print(f"Куплено {amount:.4f} {code} за {cost:.2f} USD")

                elif command == "sell":
                    require_arguments(args, ("currency", "amount"))

                    code = args["currency"].upper()
                    amount = float(args["amount"])
                    revenue = app.sell(code, amount)

                    print(f"Продано {amount:.4f} {code} за {revenue:.2f} USD")

                elif command == "update-rates":
                    rates = updater.update_rates(force=True)
                    print(f"Курсы обновлены: {len(rates)} валютных пар")

                elif command == "get-rate":
                    require_arguments(args, ("currency",))

                    code = args["currency"].upper()
                    rate = updater.get_rate(code)

                    print(f"1 {code} = {rate:.6f} USD")

                elif command == "show-rates":
                    rates = updater.get_all_rates()

                    print("Актуальные валютные курсы:")
                    for pair, rate in sorted(rates.items()):
                        print(f"  {pair}: {rate:.6f}")

                else:
                    print(f"Неизвестная команда: {command}")

            except (
                ValueError,
                TypeError,
                APIError,
                RateNotFoundError,
                CurrencyNotFoundError,
                InsufficientFundsError,
            ) as error:
                print(f"Ошибка: {error}")

            except EOFError, KeyboardInterrupt:
                print("\nДо свидания!")
                break

    finally:
        scheduler.stop()


if __name__ == "__main__":
    main()
