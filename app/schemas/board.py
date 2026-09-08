from typing import Literal

from pydantic import BaseModel

class BoardRead(BaseModel):
    board_title: str
    role: Literal["owner", "manager", "assignee", "viewer"]
