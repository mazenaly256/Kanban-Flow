from pydantic import BaseModel, Field


class TaskRead(BaseModel):
    id: int
    column_id: int
    title: str
    description: str
    # index/position of the task is not required to be shown, it is just for ordering the tasks



class TaskCreate(BaseModel):
    task_title: str
    task_description: str



class TaskUpdateTitleAndDescription(BaseModel):
    new_title: str
    new_description: str



class TaskUpdatePosition(BaseModel):
    destination_column_id: int

    destination_predecessor_task_index: float = Field(
        default=-1,
        description="Index of the task immediately before the new position in the destination column. Pass -1 if moving to the very top of the column (no predecessor)."
    )

    destination_successor_task_index: float = Field(
        default=-1,
        description="Index of the task immediately after the new position in the destination column. Pass -1 if moving to the very bottom of the column (no successor)."
    )
