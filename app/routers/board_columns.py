from typing import List

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.database import get_db
from app.core.security import require_board_member, require_manager_privileges_or_higher
from app.models import BoardColumn
from app.schemas.board_column import BoardColumnRead, BoardColumnCreate

router = APIRouter(prefix="/boards/{board_id}/columns", tags=["board columns"])


@router.get(
    path="/",
    response_model=List[BoardColumnRead],
)
async def get_board_columns(board_id: int = Path(), db: AsyncSession = Depends(get_db), _ = Depends(require_board_member)):
    result = await db.execute(select(BoardColumn.id, BoardColumn.title).where(BoardColumn.board_id == board_id).order_by(BoardColumn.index))

    board_columns: list[BoardColumnRead] = []

    for column_id, column_title in result.all():
        board_columns.append(BoardColumnRead(column_id= column_id, column_title=column_title))

    return board_columns



@router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
)
async def create_board_column(board_id: int, new_column_from_request: BoardColumnCreate, _ = Depends(require_manager_privileges_or_higher), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
    select(func.max(BoardColumn.index)).where(BoardColumn.board_id == board_id)
)

    new_board_column_index = (result.scalar_one_or_none() or 0) + 1
    new_board_column = BoardColumn(board_id=board_id, title=new_column_from_request.column_title, index=new_board_column_index)

    db.add(new_board_column)
    await db.commit()
    await db.refresh(new_board_column)

    return new_board_column.id


