from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, require_owner_privileges, require_board_member
from app.models import User, UserBoardRole, Board, BoardColumn, Task
from app.schemas import BoardRead, BoardCreate, BoardDetails, BoardColumnDetails
from app.schemas.task import TaskRead

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


@router.get(
    path="/{board_id}/",
    status_code=status.HTTP_200_OK,
    response_model=BoardDetails,
    responses={
        404: {"description": "Board not found"},
        403: {"description": "Unauthorized to access this resource"},
    }
)
async def get_board_details_by_id(board_id: int, db: AsyncSession = Depends(get_db), user_board_role = Depends(require_board_member)):
    result = await db.execute(
        select(Board).where(Board.id == board_id)
        .options(
            selectinload(Board.columns)     # one single query for ALL columns across all fetched boards at once
            .selectinload(BoardColumn.tasks)    # one single query for ALL tasks across all the fetched columns at once
        )
    )   # NO 1+N query problem, and NO duplication in the retrieved data that happens in join

    board = result.scalar_one_or_none()

    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    board_details = BoardDetails(board_id=board.id, board_title=board.title, role=user_board_role.role, columns=[])

    for column in board.columns:
        board_column_details = BoardColumnDetails(column_id=column.id, column_title=column.title, tasks=[])
        for task in column.tasks:
            board_column_details.tasks.append(TaskRead(id=task.id, column_id=task.column_id, title=task.title, description=task.description))

        board_details.columns.append(board_column_details)


    return board_details


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
