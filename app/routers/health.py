from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/health")     # readiness check
async def health(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        db_ok = value == 1
    except SQLAlchemyError:
        db_ok = False

    return {"status": "ok" if db_ok else "degraded", "db_connection": db_ok}
