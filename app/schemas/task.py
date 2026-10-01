from pydantic import BaseModel, Field, ConfigDict


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)     # informs the 'model_validate' method to read values from attributes not via square brackets as dictionaries

    id: int
    column_id: int
    title: str
    description: str
    index: float    # required so frontend clients can sort tasks correctly on real-time task position changing broadcasts
    version: int    # required to be sent to the update endpoint when the client needs to update the task



class TaskCreate(BaseModel):
    task_title: str
    task_description: str



class TaskUpdateTitleAndDescription(BaseModel):
    new_title: str
    new_description: str
    version: int    # required to be sent to get compared inside the PATCH endpoint with the version of the task in the database



class TaskUpdateChangeColumnAndPositionIndex(BaseModel):
    destination_column_id: int

    destination_predecessor_task_index: float = Field(
        default=-1,
        description="Index of the task immediately before the new position in the destination column. Pass -1 if moving to the very top of the column (no predecessor)."
    )

    destination_successor_task_index: float = Field(
        default=-1,
        description="Index of the task immediately after the new position in the destination column. Pass -1 if moving to the very bottom of the column (no successor)."
    )
