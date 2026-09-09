from pydantic import BaseModel

class BoardColumnRead(BaseModel):
    column_id: int
    column_title: str


class BoardColumnCreate(BaseModel):
    column_title: str

