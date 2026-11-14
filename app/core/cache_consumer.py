from app.core.cache import cache_board_delete

import asyncio
import logging

logger = logging.getLogger(__name__)

PENDING = "0"   # delivered-but-unacked messages, from the consumer group pending list
NEW = ">"       # messages never delivered from the stream to a specific consumer group

async def cache_invalidation_consumer(redis_client):
    read_from = PENDING

    while True:
        try:
            # read messages in the 'task:events' stream for the cache invalidator consumer group
            streams_messages = await redis_client.xreadgroup(
                groupname="group-cache-invalidator",
                consumername="worker-1",
                streams={"task:events": read_from},
                count=5,    # fetch up to 5 messages (new ones for ">", my unacked ones for "0") from 'task:events' stream to 'group-cache-invalidator' consumer group
                block=2000
            )

            messages = streams_messages[0][1] if streams_messages else []  # we have only one stream we get messages from it, so streams_messages[0] = ("task:events", messages_list)

            if read_from == PENDING and not messages:  # pending list is empty
                read_from = NEW
                continue

            for message_id, data in messages:
                board_id = int(data["board_id"])
                await cache_board_delete(redis_client, board_id)
                await redis_client.xack("task:events", "group-cache-invalidator", message_id)   # deletes the message id from the pending list of the consumer group, which means that the message/event has been handled successfully



        except Exception:
            logger.exception("cache consumer failed")
            read_from = PENDING  # go back and retry whatever is still unacked. This retries even the error happens in ack only, that is at-least-once-delivery
            await asyncio.sleep(1)