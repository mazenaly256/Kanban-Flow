from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, UserBoardRole, Board
from app.schemas import BoardRead



router = APIRouter(prefix="/boards", tags=["boards"])

@router.get(
    path="/",
    response_model=List[BoardRead],
    status_code=status.HTTP_200_OK
)
async def get_boards(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Board, UserBoardRole.role).join(UserBoardRole, Board.id == UserBoardRole.board_id).where(UserBoardRole.user_id == user.id))

    user_boards: list[BoardRead] = []

    for board, role in result.all():
        user_boards.append(BoardRead(board_title=board.title, role=role))

    return user_boards



