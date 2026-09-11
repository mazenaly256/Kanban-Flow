from pydantic import BaseModel

from .task import TaskRead


class BoardColumnRead(BaseModel):
    column_id: int
    column_title: str

class BoardColumnDetails(BaseModel):
    column_id: int
    column_title: str
    tasks: list[TaskRead]

class BoardColumnCreate(BaseModel):
    column_title: str

