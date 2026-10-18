
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from labs.lab3 import repository
from labs.lab3.schemas import (
    MAX_DURATION,
    RecordCreate,
    RecordRead,
    RecordReplace,
    Status,
)

router = APIRouter(prefix="/records", tags=["Записи"])


def translate_integrity_error(exc: sqlite3.IntegrityError):
    message = str(exc)

    if "FOREIGN KEY constraint failed" in message:
        raise HTTPException(
            status_code=404,
            detail="Вказану категорію не знайдено.",
        ) from exc

    if "UNIQUE constraint failed" in message:
        raise HTTPException(
            status_code=409,
            detail="Запис із таким code вже існує.",
        ) from exc

    raise HTTPException(status_code=422, detail="Дані порушують обмеження бази.") from exc


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Отримати записи",
    description="Фільтрація за категорією, статусом і тривалістю. Пошук за буквальним підрядком у title.",
)
def read_records(
    category_id: int | None = Query(None, gt=0, description="ID категорії"),
    status_filter: Status | None = Query(
        None, alias="status", description="Статус запису"
    ),
    min_value: float | None = Query(
        None, ge=0, le=MAX_DURATION, description="Мінімальна тривалість у хвилинах"
    ),
    q: str | None = Query(
        None, min_length=1, max_length=120, description="Підрядок у назві"
    ),
    limit: int = Query(20, ge=1, le=100, description="Максимум результатів"),
    offset: int = Query(0, ge=0, description="Кількість пропущених записів"),
):
    return repository.search_records(
        category_id=category_id,
        status=status_filter,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис за ID",
    responses={404: {"description": "Запис не знайдено"}},
)
def read_record(record_id: int = Path(gt=0)):
    record = repository.get_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Запис не знайдено.")
    return record


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запис",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Дублікат коду"},
    },
)
def create_record(data: RecordCreate):
    try:
        record_id = repository.create_record(**data.model_dump())
    except sqlite3.IntegrityError as exc:
        translate_integrity_error(exc)

    return repository.get_record(record_id)


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити запис",
    responses={
        404: {"description": "Запис або категорію не знайдено"},
        409: {"description": "Дублікат коду"},
    },
)
def replace_record(
    data: RecordReplace,
    record_id: int = Path(gt=0),
):
    try:
        repository.update_record(record_id, **data.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        translate_integrity_error(exc)

    record = repository.get_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Запис не знайдено.")
    return record


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    responses={404: {"description": "Запис не знайдено"}},
)
def remove_record(record_id: int = Path(gt=0)):
    try:
        repository.delete_record(record_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Пакетно створити записи",
    description="Приймає від 1 до 100 записів. У разі помилки пакет не зберігається.",
    responses={
        404: {"description": "Одну з категорій не знайдено"},
        409: {"description": "Дублікат коду в базі або пакеті"},
    },
)
def create_records_bulk(
    records: Annotated[
        list[RecordCreate],
        Body(min_length=1, max_length=100, description="Від 1 до 100 записів"),
    ],
):
    items = [item.model_dump() for item in records]
    codes = [item["code"] for item in items]

    if len(codes) != len(set(codes)):
        raise HTTPException(
            status_code=409,
            detail="Пакет містить повторювані значення code.",
        )

    category_ids = {item["category_id"] for item in items}
    existing_ids = {item["id"] for item in repository.get_categories()}
    missing_ids = category_ids - existing_ids

    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Категорії не знайдено: {sorted(missing_ids)}",
        )

    try:
        repository.create_records_batch(items)
    except sqlite3.IntegrityError as exc:
        translate_integrity_error(exc)

    return [repository.get_record_by_code(code) for code in codes]
