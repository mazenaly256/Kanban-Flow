from pydantic import BaseModel

class TaskRead(BaseModel):
    id: int
    column_id: int
    title: str
    description: str
    # index/position of the task is not required to be shown, it is just for ordering the tasks



class TaskCreate(BaseModel):
    task_title: str
    task_description: str
