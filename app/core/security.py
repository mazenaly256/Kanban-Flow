from datetime import datetime, timezone, timedelta
import jwt
from jwt import InvalidTokenError

from app.core.config import settings

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException

from app.core.database import get_db
from app.models import User
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

    result = await db.execute(select(User).filter(User.id == int(user_id)))
    user_from_db = result.scalar_one_or_none()

    if user_from_db is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user_from_db
