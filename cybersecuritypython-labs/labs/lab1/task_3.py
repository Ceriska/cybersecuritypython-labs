import csv
import hashlib
import json
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from shared.student import VARIANT_NUMBER

# Налаштування
MIN_LENGTH = 15

# Персональна сіль.
PERSONAL_SALT = str(VARIANT_NUMBER).zfill(5)

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.csv"
LOG_FILE = DATA_DIR / "log.json"

# Власний виняток
class ValidationError(Exception):
    pass

#Створює SHA-384 хеш від конкатенації пароля та солі.
def generate_hash(password: str, salt: str = "00000") -> str:

    if password is None or password == "":
        raise ValueError("Пароль не може бути порожнім.")

    if salt is None or salt == "":
        raise ValueError("Сіль не може бути порожньою.")

    if len(password) < MIN_LENGTH:
        raise ValidationError(
            f"Пароль повинен містити щонайменше {MIN_LENGTH} символів."
        )

    value = password + salt

    hash_object = hashlib.sha384(value.encode("utf-8"))

    return hash_object.hexdigest()

# Користувачі для реєстрації
users_to_register = (
    ("user01", "1234567890Poiuyt&"),
    ("user02", "Password02082003^"),
    ("user03", "Qwerty987654321#"),
    ("user04", "AdminPassword4!"),
    ("user05", "Cybermasons105%"),
    ("user06", "CyberSecurity6&"),
    ("user07", "VerysecureIthink7*"),
    ("user08", "Pythonpassword8!"),
    ("user09", "KB206password@lol"),
    ("user10", "ProtectedPassword10#"),
)

# Створення користувача
def create_user(username: str, password: str) -> tuple:

    if username is None or username == "":
        raise ValueError("Логін не може бути порожнім.")

    hash_value = generate_hash(
        password,
        PERSONAL_SALT,
    )

    return username, hash_value

# Створення CSV-бази
def create_users(users_list) -> None:

    try:
        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        with USERS_FILE.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.writer(file)

            for username, password in users_list:
                try:
                    user_data = create_user(
                        username,
                        password,
                    )

                    writer.writerow(user_data)

                except ValidationError as error:
                    print(
                        f"Користувач {username}: ValidationError: {error}"
                    )

                except ValueError as error:
                    print(
                        f"Користувач {username}: ValueError: {error}"
                    )

    except FileNotFoundError as error:
        print(f"FileNotFoundError: {error}")

    except PermissionError as error:
        print(f"PermissionError: {error}")

    except IOError as error:
        print(f"IOError: {error}")

# Читання CSV-бази
def read_users() -> list:

    users_db = []

    try:
        with USERS_FILE.open(
            "r",
            newline="",
            encoding="utf-8",
        ) as file:

            reader = csv.reader(file)

            for row in reader:
                if len(row) == 2:
                    username, password_hash = row

                    users_db.append(
                        (username, password_hash)
                    )

    except FileNotFoundError as error:
        print(f"FileNotFoundError: {error}")

    except PermissionError as error:
        print(f"PermissionError: {error}")

    except IOError as error:
        print(f"IOError: {error}")

    return users_db

# Виведення бази користувачів
def print_users_db(users_db: list) -> None:

    print()
    print("БАЗА КОРИСТУВАЧІВ")
    print()

    print(
        f"{'№':<5}"
        f"{'Логін':<15}"
        f"{'SHA-384 хеш':<70}"
    )
    print()

    for number, (username, password_hash) in enumerate(
        users_db,
        start=1,
    ):
        print(
            f"{number:<5}"
            f"{username:<15}"
            f"{password_hash:<70}"
        )

# Декоратор логування
def log_event(function):

    @wraps(function)
    def wrapper(username, password):
        result = "failure"

        try:
            login_result = function(
                username,
                password,
            )

            if login_result:
                result = "success"

            return login_result

        finally:
            log_data = {
                "event": "login",
                "user": username,
                "result": result,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),

                "args": [],
                "kwargs": {},
            }

            try:
                DATA_DIR.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                if LOG_FILE.exists():
                    with LOG_FILE.open(
                        "r",
                        encoding="utf-8",
                    ) as file:
                        try:
                            logs = json.load(file)
                        except json.JSONDecodeError:
                            logs = []
                else:
                    logs = []

                logs.append(log_data)

                with LOG_FILE.open(
                    "w",
                    encoding="utf-8",
                ) as file:
                    json.dump(
                        logs,
                        file,
                        indent=4,
                        ensure_ascii=False,
                    )

            except FileNotFoundError as error:
                print(f"Log FileNotFoundError: {error}")

            except PermissionError as error:
                print(f"Log PermissionError: {error}")

            except IOError as error:
                print(f"Log IOError: {error}")

    return wrapper

# Перевірка логіна та пароля
@log_event
def login(username: str, password: str) -> bool:

    if username is None or username == "":
        raise ValueError("Логін не може бути порожнім.")

    if password is None or password == "":
        raise ValueError("Пароль не може бути порожнім.")

    try:
        users_db = read_users()

        for saved_username, saved_hash in users_db:

            if saved_username == username:

                password_hash = generate_hash(
                    password,
                    PERSONAL_SALT,
                )

                return password_hash == saved_hash

        return False

    except FileNotFoundError as error:
        print(f"FileNotFoundError: {error}")
        return False

    except PermissionError as error:
        print(f"PermissionError: {error}")
        return False

    except IOError as error:
        print(f"IOError: {error}")
        return False

    except ValidationError as error:
        print(f"ValidationError: {error}")
        return False

    except ValueError as error:
        print(f"ValueError: {error}")
        return False

# Головна функція
def main():

    print()
    print("Система реєстрації та автентифікації")
    print()

    print(f"Варіант: {VARIANT_NUMBER}")
    print("Алгоритм хешування: SHA-384")
    print(f"Мінімальна довжина пароля: {MIN_LENGTH}")
    print(f"Персональна сіль: {PERSONAL_SALT}")

    # Створення бази
    print()
    print("Створення бази користувачів")

    create_users(users_to_register)

    # Читання бази
    users_db = read_users()

    print_users_db(users_db)

    # Перевірка автентифікації
    print()
    print("Перевірка автентифікації")
    print()

    test_cases = (
        ("user01", "1234567890Poiuyt&"),
        ("user01", "WrongPassword123!"),
        ("user05", "Cybermasons105%"),
        ("unknown_user", "1234567890Poiuyt&!"),
    )

    for username, password in test_cases:

        try:
            result = login(
                username,
                password,
            )

            if result:
                print(
                    f"user={username:<20} SUCCESS"
                )
            else:
                print(
                    f"user={username:<20} FAILURE"
                )

        except ValueError as error:
            print(
                f"user={username:<20} -> ERROR: {error}"
            )

        except ValidationError as error:
            print(
                f"user={username:<20} -> ERROR: {error}"
            )

    print()
    print(f"CSV база: {USERS_FILE}")
    print(f"JSON лог: {LOG_FILE}")

if __name__ == "__main__":
    main()
