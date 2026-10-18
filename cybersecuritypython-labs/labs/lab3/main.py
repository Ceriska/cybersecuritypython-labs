
from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab3.database import initialize_database
from labs.lab3.routers import categories, records
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="API навчальних записів",
    description=(
        "REST API для керування категоріями та навчальними записами. "
        "Поле value у варіанті 7 означає тривалість у хвилинах."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(categories.router)
app.include_router(records.router)


@app.get(
    "/ping",
    tags=["Службові"],
    summary="Перевірити доступність API",
)
def ping():
    return {"status": "ok"}


@app.get(
    "/student",
    tags=["Службові"],
    summary="Отримати дані студента",
)
def student():
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }
