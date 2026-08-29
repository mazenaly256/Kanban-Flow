from datetime import datetime, timezone, timedelta
import jwt
from jwt import InvalidTokenError

from app.core.config import settings


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
