
import sqlite3

from fastapi import APIRouter, HTTPException, Path, status
from pydantic import ValidationError

from labs.lab3 import repository
from labs.lab3.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Категорії"])


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Отримати список категорій",
    description="Повертає всі категорії, відсортовані за id.",
)
def read_categories():
    return repository.get_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити категорію",
    responses={409: {"description": "Категорія з такою назвою вже існує"}},
)
def create_category(data: CategoryCreate):
    try:
        category_id = repository.create_category(data.name)
    except sqlite3.IntegrityError as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(
                status_code=409,
                detail="Категорія з такою назвою вже існує.",
            ) from exc
        raise HTTPException(status_code=422, detail="Некоректні дані.") from exc

    return {"id": category_id, "name": data.name}


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити порожню категорію",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить записи"},
    },
)
def remove_category(category_id: int = Path(gt=0)):
    try:
        repository.delete_category(category_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Неможливо видалити категорію, яка містить записи.",
        ) from exc
