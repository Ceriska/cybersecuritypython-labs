
import json
import math
import sqlite3
from contextlib import closing

from labs.lab3.database import (
    BASE_DIR,
    get_connection,
    initialize_database,
)

SEED_PATH = BASE_DIR / "data" / "seed.json"
VALID_STATUSES = {"new", "in_progress", "done"}


def validate_seed(data):
    """Перевіряє структуру та вміст файлу seed.json."""
    if not isinstance(data, dict):
        raise ValueError("Корінь JSON має бути об'єктом.")

    categories = data.get("categories")
    records = data.get("records")

    if not isinstance(categories, list) or len(categories) != 3:
        raise ValueError("Потрібно вказати рівно 3 категорії.")

    if not isinstance(records, list) or len(records) != 8:
        raise ValueError("Потрібно вказати рівно 8 записів.")

    category_ids = set()
    category_names = set()

    for category in categories:
        if not isinstance(category, dict):
            raise ValueError("Категорія має бути об'єктом.")

        category_id = category.get("id")
        name = category.get("name")

        if type(category_id) is not int or category_id <= 0:
            raise ValueError(
                "ID категорії має бути додатним цілим числом."
            )

        if category_id in category_ids:
            raise ValueError("ID категорій мають бути унікальними.")

        if not isinstance(name, str) or not 2 <= len(name.strip()) <= 40:
            raise ValueError("Некоректна назва категорії.")

        normalized_name = name.strip()

        if normalized_name in category_names:
            raise ValueError("Назви категорій мають бути унікальними.")

        category_ids.add(category_id)
        category_names.add(normalized_name)

    codes = set()

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Запис має бути об'єктом.")

        # ID запису не задається: його створює SQLite.
        code = record.get("code")
        title = record.get("title")
        category_id = record.get("category_id")
        value = record.get("value")
        status = record.get("status")

        if not isinstance(code, str) or not 3 <= len(code.strip()) <= 40:
            raise ValueError("Некоректний code у записі.")

        code = code.strip()

        if code in codes:
            raise ValueError(f"Код запису {code} повторюється.")

        if not isinstance(title, str) or not 3 <= len(title.strip()) <= 120:
            raise ValueError(f"Некоректний title у записі {code}.")

        if type(category_id) is not int or category_id not in category_ids:
            raise ValueError(f"Невідома категорія у записі {code}.")

        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError(
                f"Некоректна тривалість у записі {code}."
            )

        if status not in VALID_STATUSES:
            raise ValueError(f"Некоректний статус у записі {code}.")

        codes.add(code)


def seed_database():
    """Заповнює порожню базу початковими даними."""
    try:
        data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
        validate_seed(data)

        initialize_database()

        with closing(get_connection()) as connection:
            connection.execute("BEGIN")

            try:
                category_count = connection.execute(
                    "SELECT COUNT(*) FROM categories"
                ).fetchone()[0]

                record_count = connection.execute(
                    "SELECT COUNT(*) FROM records"
                ).fetchone()[0]

                if category_count != 0 or record_count != 0:
                    connection.rollback()
                    print(
                        "База вже містить дані. Змін не внесено."
                    )
                    return

                # Категорії отримують ID із seed.json.
                connection.executemany(
                    """
                    INSERT INTO categories (id, name)
                    VALUES (?, ?)
                    """,
                    [
                        (item["id"], item["name"].strip())
                        for item in data["categories"]
                    ],
                )

                # ID записів генеруються автоматично SQLite.
                connection.executemany(
                    """
                    INSERT INTO records
                        (code, title, category_id, value, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            item["code"].strip(),
                            item["title"].strip(),
                            item["category_id"],
                            item["value"],
                            item["status"],
                        )
                        for item in data["records"]
                    ],
                )

                connection.commit()
                print("Додано 3 категорії та 8 записів.")

            except Exception:
                connection.rollback()
                raise

    except (OSError, json.JSONDecodeError, ValueError, sqlite3.Error) as error:
        print(f"Помилка початкового заповнення: {error}")


if __name__ == "__main__":
    seed_database()
