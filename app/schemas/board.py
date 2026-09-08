from typing import Literal

from pydantic import BaseModel

class BoardRead(BaseModel):
    board_id: int
    board_title: str
    role: Literal["owner", "manager", "assignee", "viewer"]



class BoardCreate(BaseModel):
    board_title: str
