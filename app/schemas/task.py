from pydantic import BaseModel

class TaskRead(BaseModel):
    task_id: int
    column_id: int
    column_title: str
    task_title: str
    task_description: str
    # index/position of the task is not required to be shown, it is just for ordering the tasks



class TaskCreate(BaseModel):
    column_id: int
    task_title: str
    task_description: str
