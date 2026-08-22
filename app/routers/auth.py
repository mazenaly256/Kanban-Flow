import bcrypt
from fastapi import APIRouter, Depends
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User
from app.schemas import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead
)
async def register(user_request_model: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(
        email=user_request_model.email,
        username=user_request_model.username,
        hashed_password=bcrypt.hashpw(user_request_model.password.encode(), bcrypt.gensalt()).decode()
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserRead(id=new_user.id, email=new_user.email, username=new_user.username)