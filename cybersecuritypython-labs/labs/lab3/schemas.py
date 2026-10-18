
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Status = Literal["new", "in_progress", "done"]

MAX_DURATION = 1.7976931348623157e308


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class CategoryCreate(StrictModel):
    name: str = Field(min_length=2, max_length=40)


class CategoryRead(StrictModel):
    id: int
    name: str


class RecordCreate(StrictModel):
    code: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=3, max_length=120)
    category_id: int = Field(gt=0)
    value: float = Field(ge=0, le=MAX_DURATION, allow_inf_nan=False)
    status: Status = "new"

class RecordRead(StrictModel):
    id: int
    code: str
    title: str
    category_id: int
    category_name: str
    value: float
    status: Status

class RecordReplace(StrictModel):
    code: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=3, max_length=120)
    category_id: int = Field(gt=0)
    value: float = Field(ge=0, le=MAX_DURATION, allow_inf_nan=False)
    status: Status