import asyncio
import logging

from sqlalchemy import select, update, func

from app.models import OutboxEvent
from app.websockets import broadcast_to_board_subscribers

logger = logging.getLogger(__name__)

async def relay_loop(session_factory, redis_client):
    while True:
        try:
            async with session_factory() as db:
                rows = (await db.execute(
                    select(OutboxEvent.id, OutboxEvent.board_id, OutboxEvent.payload)
                    .where(OutboxEvent.published_at.is_(None))  # lets Postgres use the partial index
                    .order_by(OutboxEvent.id)
                    .limit(20)
                )).all()

            for row in rows:
                await redis_client.delete(f"board:{row.board_id}")
                await broadcast_to_board_subscribers(row.board_id, row.payload)
                async with session_factory() as db:
                    await db.execute(update(OutboxEvent).where(OutboxEvent.id == row.id).values(published_at=func.now()))
                    await db.commit()

            if not rows:
                await asyncio.sleep(0.1)

        except Exception:
            logger.exception("relay iteration failed")
            await asyncio.sleep(1)