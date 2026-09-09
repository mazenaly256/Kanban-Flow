from datetime import datetime, timezone, timedelta
import jwt
from jwt import InvalidTokenError

from app.core.config import settings

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException

from app.core.database import get_db
from app.models import User, UserBoardRole
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


HASHING_ALGORITHM = "HS256"
JWT_SECRET_KEY = settings.jwt_secret_key



def issue_jwt_access_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)

    payload = {
        "sub": str(user_id),
        "exp": exp
    }

    return jwt.encode(payload=payload, key=JWT_SECRET_KEY, algorithm=HASHING_ALGORITHM)


def decode_jwt_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(jwt=token, key=JWT_SECRET_KEY, algorithms=[HASHING_ALGORITHM])

    except InvalidTokenError:  # To catch expired, tampered, malformed or any invalid tokens
        return None

    return payload


bearer_scheme = HTTPBearer()        # executing it results in extracting Authorization header from request

async def get_current_user(authorization_header: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: AsyncSession = Depends(get_db)) -> User:
    access_token = authorization_header.credentials

    payload = decode_jwt_access_token(access_token)

    if payload is not None:
        user_id = payload.get('sub')

    else:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user_from_db = result.scalar_one_or_none()

    if user_from_db is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user_from_db


async def require_board_member(board_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):   # FastAPI detects that inside the endpoint there is board_id parameter and also required here so it injects its value automatically
    result = await db.execute(
        select(UserBoardRole).where(UserBoardRole.board_id == board_id, UserBoardRole.user_id == user.id)
    )

    user_board_role = result.scalar_one_or_none()

    if user_board_role is None:
        raise HTTPException(status_code=403, detail="Access denied, you are not permitted to access this board.")

    else:
        return user_board_role


async def require_owner_privileges(user_board_role: UserBoardRole = Depends(require_board_member)):
    if user_board_role.role != "owner":
        raise HTTPException(status_code=403, detail="Access Denied, This action requires owner privileges.")



async def require_manager_privileges_or_higher(user_board_role: UserBoardRole = Depends(require_board_member)):
    if user_board_role.role != "owner" and user_board_role.role != "manager":
        raise HTTPException(status_code=403, detail="Access Denied, This action requires at least manager privileges.")



async def require_assignee_privileges_or_higher(user_board_role: UserBoardRole = Depends(require_board_member)):
    if user_board_role.role != "owner" and user_board_role.role != "manager" and user_board_role.role != "assignee":
        raise HTTPException(status_code=403, detail="Access Denied, This action requires at least assignee privileges, viewers can not take this action.")
