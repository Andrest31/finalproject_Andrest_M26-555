"""Консольный интерфейс ValutaTrade Hub."""

import shlex

from valutatrade_hub.core.usecases import ValutaTrade


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
    app = ValutaTrade()

    print("ValutaTrade Hub")
    print("Введите help для списка команд.")

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

            else:
                print(f"Неизвестная команда: {command}")

        except (ValueError, TypeError) as error:
            print(f"Ошибка: {error}")

        except EOFError, KeyboardInterrupt:
            print("\nДо свидания!")
            break
