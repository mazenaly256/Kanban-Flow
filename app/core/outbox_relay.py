import asyncio
import logging

from sqlalchemy import select, update, func

from app.core.cache import cache_board_delete
from app.core.database import AsyncSessionLocal
from app.websockets import broadcast_to_board_subscribers
from app.models import OutboxEvent


logger = logging.getLogger(__name__)

async def relay_loop(redis_client):
    while True:
        try:
            async with AsyncSessionLocal() as db:
                rows = (await db.execute(
                    select(OutboxEvent.id, OutboxEvent.board_id, OutboxEvent.payload)
                    .where(OutboxEvent.published_at.is_(None))
                    .order_by(OutboxEvent.id)
                    .limit(20)
                )).all()
                # where(published_at is None) lets Postgres use the partial index

            for row in rows:    # loop over all pending tasks (not published)
                await cache_board_delete(redis_client, row.board_id)
                await broadcast_to_board_subscribers(row.board_id, row.payload)

                async with AsyncSessionLocal() as db:
                    await db.execute(update(OutboxEvent).where(OutboxEvent.id == row.id).values(published_at=func.now()))
                    await db.commit()

            if not rows:
                await asyncio.sleep(0.1)

        except Exception:
            logger.exception("relay iteration failed")
            await asyncio.sleep(1)