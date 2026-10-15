import hashlib
import secrets
from datetime import UTC, datetime


class User:
    """Пользователь системы ValutaTrade Hub."""

    def __init__(
        self,
        user_id: int,
        username: str,
        password: str | None = None,
        hashed_password: str | None = None,
        salt: str | None = None,
        registration_date: datetime | None = None,
    ):
        self._user_id = user_id
        self._username = ""
        self.username = username
        self._hashed_password = ""
        self._salt = salt or secrets.token_hex(16)
        self._registration_date = registration_date or datetime.now(UTC)

        if hashed_password is not None:
            self._hashed_password = hashed_password
        elif password is not None:
            self.change_password(password)
        else:
            raise ValueError("Необходимо указать пароль или его хеш")

    @property
    def user_id(self) -> int:
        """Возвращает идентификатор пользователя."""
        return self._user_id

    @property
    def username(self) -> str:
        """Возвращает имя пользователя."""
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def registration_date(self) -> datetime:
        """Возвращает дату регистрации."""
        return self._registration_date

    def change_password(self, new_password: str) -> None:
        """Меняет пароль, сохраняя его хеш с новой солью."""
        if not isinstance(new_password, str) or len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        self._salt = secrets.token_hex(16)
        self._hashed_password = hashlib.sha256(
            (new_password + self._salt).encode("utf-8")
        ).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Проверяет пароль пользователя."""
        if not isinstance(password, str):
            return False

        password_hash = hashlib.sha256(
            (password + self._salt).encode("utf-8")
        ).hexdigest()

        return secrets.compare_digest(password_hash, self._hashed_password)

    def get_user_info(self) -> dict:
        """Возвращает публичную информацию о пользователе."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def to_dict(self) -> dict:
        """Сериализует пользователя для хранения в JSON."""
        return {
            **self.get_user_info(),
            "hashed_password": self._hashed_password,
            "salt": self._salt,
        }

    @classmethod
    def from_dict(cls, data: dict) -> User:
        """Восстанавливает пользователя из JSON."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=datetime.fromisoformat(data["registration_date"]),
        )
