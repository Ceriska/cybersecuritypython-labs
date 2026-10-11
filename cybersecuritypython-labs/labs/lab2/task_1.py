import hashlib
import hmac
import os
import re

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


PBKDF2_ITERATIONS = 200_000
SESSION_TIMEOUT_SEC = 900


class User:
    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z][A-Za-z0-9_]{2,63}@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
    )

    def __init__(
        self,
        username: str,
        email: str,
        role: str,
        active: bool = True,
    ) -> None:
        self.username = username
        self.email = email
        self.role = role
        self.active = active

        self.__password_hash: bytes = b""
        self.__password_salt: bytes = b""

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Email має бути рядком.")

        if not self.EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Некоректний формат email.")

        self.__email = value

    def set_password(self, password: str) -> None:
        if not isinstance(password, str):
            raise TypeError("Пароль має бути рядком.")

        if not password:
            raise ValueError("Пароль не може бути порожнім.")

        self.__password_salt = os.urandom(16)
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        if not isinstance(password, str):
            return False

        if not self.__password_hash or not self.__password_salt:
            return False

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

        return hmac.compare_digest(
            self.__password_hash,
            password_hash,
        )

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        return (
            f"User(username='{self.username}', "
            f"email='{self.email}', "
            f"role='{self.role}', "
            f"active={self.active})"
        )


class Admin(User):
    def __init__(
        self,
        username: str,
        email: str,
        role: str = "admin",
        active: bool = True,
        permissions=None,
    ) -> None:
        super().__init__(username, email, role, active)
        self.permissions = set(permissions) if permissions is not None else set()

    def grant_permission(self, permission: str) -> None:
        if not isinstance(permission, str):
            raise TypeError("Дозвіл має бути рядком.")

        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        permissions = ", ".join(sorted(self.permissions))
        return (
            f"Admin(username='{self.username}', "
            f"email='{self.email}', "
            f"role='{self.role}', "
            f"active={self.active}, "
            f"permissions=[{permissions}])"
        )


class Session:
    def __init__(
        self,
        ip: str,
        login_time: datetime | None = None,
        last_activity: datetime | None = None,
    ) -> None:
        self.ip = ip

        now = datetime.now(timezone.utc)

        self.login_time = login_time or now
        self.last_activity = last_activity or self.login_time

        self._validate_datetime(self.login_time)
        self._validate_datetime(self.last_activity)

    @staticmethod
    def _validate_datetime(value: datetime) -> None:
        if value.tzinfo is None:
            raise ValueError("Час має містити часовий пояс.")

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        if not isinstance(timeout_sec, int):
            raise TypeError("timeout_sec має бути цілим числом.")

        if timeout_sec <= 0:
            raise ValueError("timeout_sec має бути додатним.")

        now = datetime.now(timezone.utc)
        elapsed = now - self.last_activity

        return elapsed <= timedelta(seconds=timeout_sec)


@dataclass
class AuditRecord:
    timestamp: datetime
    username: str
    action: str


class AuditLog:
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        self.records.append(
            AuditRecord(
                timestamp=datetime.now(timezone.utc),
                username=username,
                action=action,
            )
        )

    def show_all(self) -> None:
        if not self.records:
            print("AuditLog порожній.")
            return

        for record in self.records:
            print(
                f"{record.timestamp.isoformat()} | "
                f"user={record.username} | "
                f"action={record.action}"
            )


class UserAccount:
    ALLOWED_KEYS = {"user", "session", "audit_log"}

    def __init__(
        self,
        user: User,
        session: Session | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        if not isinstance(user, User):
            raise TypeError("user має бути об'єктом User.")

        if session is not None and not isinstance(session, Session):
            raise TypeError("session має бути об'єктом Session.")

        if audit_log is not None and not isinstance(audit_log, AuditLog):
            raise TypeError("audit_log має бути об'єктом AuditLog.")

        self.user = user
        self.session = session
        self.audit_log = audit_log or AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        if username != self.user.username:
            self.audit_log.add_log(username, "login_failure")
            return False

        if not self.user.active:
            self.audit_log.add_log(username, "login_failure")
            return False

        if not self.user.check_password(password):
            self.audit_log.add_log(username, "login_failure")
            return False

        self.session = Session(ip)
        self.session.touch()

        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        if self.session is None:
            return False

        if not self.session.is_active(SESSION_TIMEOUT_SEC):
            return False

        return True

    def logout(self) -> None:
        if self.session is not None:
            self.audit_log.add_log(
                self.user.username,
                "logout",
            )
            self.session = None

    def __getitem__(self, key: str):
        if key not in self.ALLOWED_KEYS:
            raise KeyError(f"Невідомий ключ: {key}")

        return getattr(self, key)

    def __setitem__(self, key: str, value) -> None:
        if key not in self.ALLOWED_KEYS:
            raise KeyError(f"Невідомий ключ: {key}")

        if key == "user" and not isinstance(value, User):
            raise TypeError("user має бути об'єктом User.")

        if key == "session" and value is not None:
            if not isinstance(value, Session):
                raise TypeError("session має бути об'єктом Session.")

        if key == "audit_log" and not isinstance(value, AuditLog):
            raise TypeError("audit_log має бути об'єктом AuditLog.")

        setattr(self, key, value)


def main() -> None:
    print("Демонстрація завдання 1")

    # Створення користувача
    user = User(
        username="student",
        email="student_01@example.com",
        role="user",
    )

    user.set_password("SecretPassword123")

    print("\n1. Користувач:")
    print(user)

    # Перевірка пароля-
    print("\n2. Перевірка пароля:")

    print(
        "Правильний пароль:",
        user.check_password("SecretPassword123"),
    )

    print(
        "Неправильний пароль:",
        user.check_password("WrongPassword"),
    )

    # Email
    print("\n3. Зміна email:")

    user.email = "new_student@example.com"
    print("Новий email:", user.email)

    try:
        user.email = "invalid-email"
    except ValueError as error:
        print("Помилка валідації:", error)

    # Адміністратор
    print("\n4. Адміністратор:")

    admin = Admin(
        username="admin",
        email="admin@example.com",
        permissions={"read"},
    )

    admin.set_password("AdminPassword123")

    admin.grant_permission("write")
    admin.grant_permission("delete")

    print(admin)

    print(
        "Має permission 'write':",
        admin.has_permission("write"),
    )

    admin.revoke_permission("delete")

    print("Після revoke:", admin)

    # UserAccount та AuditLog
    print("\n5. UserAccount:")

    account = UserAccount(user)

    print("Невдалий вхід:")
    result = account.login(
        username="student",
        password="WrongPassword",
        ip="192.168.1.10",
    )
    print("Результат:", result)

    print("\nУспішний вхід:")
    result = account.login(
        username="student",
        password="SecretPassword123",
        ip="192.168.1.10",
    )
    print("Результат:", result)
    print("Авторизований:", account.is_authenticated())

    # __getitem__ / __setitem__
    print("\n6. Доступ через []:")

    print("account['user']:", account["user"])
    print("account['session']:", account["session"])

    # Демонстрація таймауту
    print("\n7. Таймаут сеансу:")

    if account.session is not None:
        account.session.last_activity = (
            datetime.now(timezone.utc)
            - timedelta(seconds=SESSION_TIMEOUT_SEC + 1)
        )

    print(
        "Авторизований після таймауту:",
        account.is_authenticated(),
    )

    # Вихід
    print("\n8. Вихід із системи:")

    account.logout()

    print("Сеанс:", account.session)
    print("Авторизований:", account.is_authenticated())

    print("\n9. AuditLog:")

    account.audit_log.show_all()


if __name__ == "__main__":
    main()
