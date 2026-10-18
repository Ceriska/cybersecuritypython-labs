
import sqlite3
from contextlib import closing

from labs.lab3.database import get_connection

VALID_STATUSES = {"new", "in_progress", "done"}


def create_category(name):
    with closing(get_connection()) as con:
        try:
            cur = con.execute(
                "INSERT INTO categories (name) VALUES (?)", (name,)
            )
            category_id = cur.lastrowid
            con.commit()
            return category_id
        except Exception:
            con.rollback()
            raise


def get_categories():
    with closing(get_connection()) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]


def delete_category(category_id):
    with closing(get_connection()) as con:
        try:
            cur = con.execute(
                "DELETE FROM categories WHERE id = ?", (category_id,)
            )
            if cur.rowcount == 0:
                raise LookupError("Категорію не знайдено.")
            con.commit()
        except Exception:
            con.rollback()
            raise


def create_record(code, title, category_id, value, status="new"):
    with closing(get_connection()) as con:
        try:
            cur = con.execute(
                """
                INSERT INTO records
                    (code, title, category_id, value, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (code, title, category_id, value, status),
            )
            record_id = cur.lastrowid
            con.commit()
            return record_id
        except Exception:
            con.rollback()
            raise


def get_record(record_id):
    with closing(get_connection()) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            """
            SELECT r.id, r.code, r.title, r.category_id,
                   c.name AS category_name, r.value, r.status
            FROM records AS r
            JOIN categories AS c ON c.id = r.category_id
            WHERE r.id = ?
            """,
            (record_id,),
        ).fetchone()
        return dict(row) if row else None


def list_records(
    category_id=None,
    status=None,
    search=None,
    page=1,
    page_size=10,
):
    if type(page) is not int or page < 1:
        raise ValueError("Сторінка має бути додатним цілим числом.")

    if type(page_size) is not int or not 1 <= page_size <= 100:
        raise ValueError("Розмір сторінки має бути від 1 до 100.")

    if status is not None and status not in VALID_STATUSES:
        raise ValueError("Некоректний статус.")

    conditions = []
    params = []

    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)

    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)

    if search:
        conditions.append("(r.code LIKE ? OR r.title LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    with closing(get_connection()) as con:
        con.row_factory = sqlite3.Row

        total = con.execute(
            "SELECT COUNT(*) FROM records AS r" + where, params
        ).fetchone()[0]

        rows = con.execute(
            """
            SELECT r.id, r.code, r.title, r.category_id,
                   c.name AS category_name, r.value, r.status
            FROM records AS r
            JOIN categories AS c ON c.id = r.category_id
            """
            + where
            + " ORDER BY r.id LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()

        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }


def update_record(record_id, code, title, category_id, value, status):
    with closing(get_connection()) as con:
        try:
            cur = con.execute(
                """
                UPDATE records
                SET code = ?, title = ?, category_id = ?,
                    value = ?, status = ?
                WHERE id = ?
                """,
                (code, title, category_id, value, status, record_id),
            )

            if cur.rowcount == 0:
                raise LookupError("Запис не знайдено.")

            con.commit()
        except Exception:
            con.rollback()
            raise


def delete_record(record_id):
    with closing(get_connection()) as con:
        try:
            cur = con.execute(
                "DELETE FROM records WHERE id = ?", (record_id,)
            )

            if cur.rowcount == 0:
                raise LookupError("Запис не знайдено.")

            con.commit()
        except Exception:
            con.rollback()
            raise


def create_records_batch(records):
    if not records:
        raise ValueError("Список записів порожній.")

    with closing(get_connection()) as con:
        try:
            con.executemany(
                """
                INSERT INTO records
                    (code, title, category_id, value, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        item["code"],
                        item["title"],
                        item["category_id"],
                        item["value"],
                        item["status"],
                    )
                    for item in records
                ],
            )
            con.commit()
            return len(records)
        except Exception:
            con.rollback()
            raise


def search_records(
    category_id=None,
    status=None,
    min_value=None,
    q=None,
    limit=20,
    offset=0,
):
    conditions = []
    params = []

    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)

    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)

    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)

    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    with closing(get_connection()) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            """
            SELECT r.id, r.code, r.title, r.category_id,
                   c.name AS category_name, r.value, r.status
            FROM records AS r
            JOIN categories AS c ON c.id = r.category_id
            """
            + where
            + " ORDER BY r.id ASC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

        return [dict(row) for row in rows]


def get_record_by_code(code):
    with closing(get_connection()) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            """
            SELECT r.id, r.code, r.title, r.category_id,
                   c.name AS category_name, r.value, r.status
            FROM records AS r
            JOIN categories AS c ON c.id = r.category_id
            WHERE r.code = ?
            """,
            (code,),
        ).fetchone()

        return dict(row) if row else None
