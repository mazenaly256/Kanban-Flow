from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.database import get_db
from app.schemas import UserRead
from app.core.security import get_current_user
from app.models import User


router = APIRouter(prefix="/users", tags=["users"])

@router.get(
    path="/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid Token."},
    }
)
async def get_logged_in_user_details(user: User = Depends(get_current_user)):
    return user


@router.get(
    path="/{email_address}/",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid Token."},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found."}
    }
)
async def get_user_details_by_email_address(email_address: EmailStr, db: AsyncSession = Depends(get_db), _ = Depends(get_current_user)):
    result = await db.execute(
        select(User).where(User.email == email_address)
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user