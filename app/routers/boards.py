from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, require_owner_privileges
from app.models import User, UserBoardRole, Board
from app.schemas import BoardRead, BoardCreate



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
        user_boards.append(BoardRead(board_id=board.id, board_title=board.title, role=role))

    return user_boards



@router.post(
    path="/",
    status_code=status.HTTP_201_CREATED
)
async def create_board(new_board_from_request: BoardCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    new_board = Board(title=new_board_from_request.board_title)

    db.add(new_board)
    await db.flush()    # actually connects to the DB and apply pending changes that were only in memory in a transaction and retrieves generated values (like IDs) back into the ORM objects.

    owner_role = UserBoardRole(user_id=user.id, board_id=new_board.id, role="owner")

    db.add(owner_role)

    await db.commit()   # tries to persist the changes to database in atomicity, both inserting new board and inserting the user-role for the board

    await db.refresh(new_board)

    return BoardRead(board_id=new_board.id, board_title=new_board.title, role="owner")



@router.delete(
    path="/{board_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Board not found"},
        403: {"description": "Unauthorized to delete this resource"},
        204: {"description": "Deleted Successfully"}
    }
)
async def delete_board(board_id: int = Path(), db: AsyncSession = Depends(get_db), _ = Depends(require_owner_privileges)):
    result = await db.execute(
        select(Board).where(Board.id == board_id)
    )
    board = result.scalar_one_or_none()

    if not board:
        raise HTTPException(status_code=404, detail="Board Not Found")


    await db.delete(board)
    await db.commit()

