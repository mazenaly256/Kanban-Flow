import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.database import get_db
from app.core.security import issue_jwt_access_token
from app.models import User
from app.schemas import UserCreate, UserRead, LoginResponse, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Email/Username Already Exists"},
        status.HTTP_201_CREATED: {"description": "Successful Registration"}
    }
)
async def register(user_request_model: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(
        email=user_request_model.email,
        username=user_request_model.username,
        hashed_password= (await run_in_threadpool(
            bcrypt.hashpw,
            user_request_model.password.encode(),
            bcrypt.gensalt()
        )).decode()     # .decode() converts the hashing result to a string
    )

    db.add(new_user)

    try:
        await db.commit()

    except IntegrityError:
        await db.rollback()     # clears SQLAlchemy's in-memory pending state and sends ROLLBACK to Postgres,
                                # discarding the aborted transaction so the underlying connection is safe to reuse (by this session or, once pooled, another)

        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username are already registered")


    await db.refresh(new_user)

    return UserRead(id=new_user.id, email=new_user.email, username=new_user.username)



@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=LoginResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid Email or Password."},
        status.HTTP_200_OK: {"description": "Successful Login"}
    }
)
async def login(login_request_model: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == login_request_model.email)
    )
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or username is wrong")

    is_valid_password: bool = await run_in_threadpool(      # Uses a thread from the threadpool to prevent blocking the main single thread of the main single event loop
        bcrypt.checkpw,
        login_request_model.password.encode(),
        user.hashed_password.encode()
    )

    if not is_valid_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong Email or password")


    token = issue_jwt_access_token(user.id)

    return LoginResponse(access_token=token, token_type="bearer")