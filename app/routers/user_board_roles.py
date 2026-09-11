from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import require_owner_privileges
from app.models import User, UserBoardRole, Board
from app.schemas.board import BoardMemberRead, BoardMemberCreate, BoardMemberUpdate


router = APIRouter(prefix="/boards/{board_id}/members", tags=["board membership"])


@router.get(
    path="/",
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
    path="/",
    status_code=status.HTTP_201_CREATED
)
async def add_new_member_role(new_member_model: BoardMemberCreate, board_id: int = Path(), db: AsyncSession = Depends(get_db), _ = Depends(require_owner_privileges)):
    result = await db.execute(
        select(Board).where(Board.id == board_id)
    )
    board = result.scalar_one_or_none()

    if not board:
        raise HTTPException(status_code=404, detail="Board Not Found")

    result = await db.execute(
        select(User).where(User.id == new_member_model.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    new_user_board_role = UserBoardRole(user_id=new_member_model.user_id, board_id=board_id, role=new_member_model.role)
    db.add(new_user_board_role)

    try:
        await db.commit()

    except IntegrityError:
        await db.rollback()     # resetting the connection's transaction state so it's safe to reuse
        raise HTTPException(status_code=409, detail="User already has a role on this board")


@router.patch(
    path="/{user_id}/",
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
    path="/{user_id}/",
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