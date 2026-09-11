from typing import Literal

from pydantic import BaseModel

class BoardRead(BaseModel):
    board_id: int
    board_title: str
    role: Literal["owner", "manager", "assignee", "viewer"]



class BoardCreate(BaseModel):
    board_title: str


class BoardMemberRead(BaseModel):
    user_id: int
    role: Literal["owner", "manager", "assignee", "viewer"]


class BoardMemberCreate(BaseModel):
    user_id: int
    role: Literal["manager", "assignee", "viewer"]


class BoardMemberUpdate(BaseModel):
    new_role: Literal["manager", "assignee", "viewer"]