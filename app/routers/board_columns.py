from typing import List

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_board_member
from app.models import BoardColumn
from app.schemas.board_column import BoardColumnRead

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


