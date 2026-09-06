from fastapi import APIRouter, Depends
from starlette import status

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