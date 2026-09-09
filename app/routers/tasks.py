from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.database import get_db
from app.core.security import require_board_member, require_manager_privileges_or_higher
from app.models import Task, BoardColumn
from app.schemas.task import TaskRead, TaskCreate, TaskUpdateTitleAndDescription, TaskUpdatePositionIndex

router = APIRouter(prefix="/boards/{board_id}/columns/{column_id}", tags=["tasks"])


@router.get(
    path="/",
    response_model=List[TaskRead],
)
async def get_all_tasks_in_column(board_id: int, column_id: int, db: AsyncSession = Depends(get_db), _ = Depends(require_board_member)):
    result = await db.execute(
        select(Task).where(Task.column_id == column_id).order_by(Task.index)
    )

    all_tasks = result.scalars().all()

    return all_tasks



@router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
)
async def create_new_task(task_create_dto: TaskCreate, board_id: int, column_id: int, _ = Depends(require_manager_privileges_or_higher), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BoardColumn).where(BoardColumn.id == column_id, BoardColumn.board_id == board_id)
    )

    column = result.scalar_one_or_none()

    if column is None:
        raise HTTPException(status_code=404, detail="Column not found in the target board")

    result = await db.execute(
        select(func.max(Task.index)).where(Task.column_id == column_id)
    )

    new_task_index = (result.scalar_one_or_none() or 0) + 1
    new_task = Task(column_id=column_id, title=task_create_dto.task_title, description=task_create_dto.task_description, index=new_task_index)

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task.id


@router.patch(
    path="/{task_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_task_title_and_description(task_id: int, board_id: int, column_id: int, task_update_dto: TaskUpdateTitleAndDescription, _ = Depends(require_manager_privileges_or_higher), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).join(BoardColumn, BoardColumn.id == Task.column_id).where(Task.id == task_id, Task.column_id == column_id, BoardColumn.board_id == board_id)
    )

    task: Task | None = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found in the target column and board")


    task.title = task_update_dto.new_title
    task.description = task_update_dto.new_description

    await db.commit()



@router.patch(
    path="/{task_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Reorders a task within its column.",
)
async def update_task_position_index_in_the_column(task_id: int, board_id: int, column_id: int, task_update_index_dto: TaskUpdatePositionIndex, _ = Depends(require_manager_privileges_or_higher), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).join(BoardColumn, BoardColumn.id == Task.column_id).where(Task.id == task_id, Task.column_id == column_id, BoardColumn.board_id == board_id)
    )

    task: Task | None = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found in the target column and board")

    if task_update_index_dto.destination_predecessor_task_index == -1 and task_update_index_dto.destination_successor_task_index == -1: # when the task is inserted in an empty column
        task_update_index_dto.destination_predecessor_task_index = task_update_index_dto.destination_successor_task_index = 1

    elif task_update_index_dto.destination_predecessor_task_index == -1:
        task_update_index_dto.destination_predecessor_task_index = task_update_index_dto.destination_successor_task_index - 1

    elif task_update_index_dto.destination_successor_task_index == -1:
        task_update_index_dto.destination_successor_task_index = task_update_index_dto.destination_predecessor_task_index + 1

    task.index = (task_update_index_dto.destination_predecessor_task_index + task_update_index_dto.destination_successor_task_index) / 2.0

    await db.commit()



@router.delete(
    path="/{task_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
# board_id is required for FastAPI DI container to resolve the board_id parameter in the dependencies (to authorize the access to the board)
async def delete_task(task_id: int, column_id: int, board_id: int, _ = Depends(require_manager_privileges_or_higher), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).join(BoardColumn, BoardColumn.id == Task.column_id).where(Task.id == task_id, Task.column_id == column_id, BoardColumn.board_id == board_id)
    )

    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found in the target column and board")

    await db.delete(task)
    await db.commit()
