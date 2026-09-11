from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, require_owner_privileges
from app.models import User, UserBoardRole, Board
from app.schemas import BoardRead, BoardCreate
from app.schemas.board import BoardMemberRead, BoardMemberCreate, BoardMemberUpdate

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



@router.get(
    path="/{board_id}/members/",
    status_code=status.HTTP_200_OK,
    response_model=List[BoardMemberRead]
)
async def get_all_board_members(board_id: int = Path(), db: AsyncSession = Depends(get_db), _ = Depends(require_owner_privileges)):
    result = await db.execute(
        select(Board).where(Board.id == board_id)
    )
    board = result.scalar_one_or_none()

    if not board:
        raise HTTPException(status_code=404, detail="Board Not Found")

    result = await db.execute(
        select(UserBoardRole).where(UserBoardRole.board_id == board_id)
    )

    all_members = result.scalars().all()

    return all_members



@router.post(
    path="/{board_id}/members/",
    status_code=status.HTTP_201_CREATED
)
async def add_new_member_role(new_member_model: BoardMemberCreate, board_id: int = Path(), db: AsyncSession = Depends(get_db), _ = Depends(require_owner_privileges)):
    result = await db.execute(
        select(Board).where(Board.id == board_id)
    )
    board = result.scalar_one_or_none()

    if not board:
        raise HTTPException(status_code=404, detail="Board Not Found")

    new_user_board_role = UserBoardRole(user_id=new_member_model.user_id, board_id=board_id, role=new_member_model.role)
    db.add(new_user_board_role)

    try:
        await db.commit()

    except IntegrityError:
        raise HTTPException(status_code=409, detail="User already has a role on this board")


@router.patch(
    path="/{board_id}/members/{user_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def change_member_role(board_id: int, user_id: int, updated_member_model: BoardMemberUpdate, db: AsyncSession = Depends(get_db), _ = Depends(require_owner_privileges)):
    result = await db.execute(
        select(UserBoardRole).where(UserBoardRole.board_id == board_id, UserBoardRole.user_id == user_id)
    )
    user_board_role: UserBoardRole = result.scalar_one_or_none()

    if not user_board_role:
        raise HTTPException(status_code=404, detail="Role of user on the requested board is not found")

    user_board_role.role = updated_member_model.new_role

    await db.commit()



@router.delete(
    path="/{board_id}/members/{user_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_member_role(board_id: int, user_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_owner_privileges)):
    result = await db.execute(
        select(UserBoardRole).where(UserBoardRole.board_id == board_id, UserBoardRole.user_id == user_id)
    )
    user_board_role: UserBoardRole = result.scalar_one_or_none()

    if not user_board_role:
        raise HTTPException(status_code=404, detail="Role of user on the requested board is not found")

    await db.delete(user_board_role)
    await db.commit()