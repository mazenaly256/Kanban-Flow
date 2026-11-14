import asyncio
import json
import logging

from app.websockets import broadcast_to_board_subscribers

logger = logging.getLogger(__name__)

PENDING = "0"   # delivered-but-unacked messages, from the consumer group pending list
NEW = ">"       # messages never delivered from the stream to a specific consumer group

async def websocket_broadcasting_consumer(redis_client):
    read_from = PENDING

    while True:
        try:
            # read messages in the 'task:events' stream for the websocket broadcaster consumer group
            streams_messages = await redis_client.xreadgroup(
                groupname="group-websocket-broadcaster",
                consumername="worker-1",
                streams={"task:events": read_from},
                count=5,
                block=2000
            )

            messages = streams_messages[0][1] if streams_messages else []   # we have only one stream here, so streams_messages[0] = ("task:events", messages_list)

            if read_from == PENDING and not messages:  # pending list is empty
                read_from = NEW
                continue

            for message_id, data in messages:
                board_id = int(data["board_id"])  # Values come back as strings from Redis
                payload = json.loads(data["payload"])  # Parse JSON string back into a dict
                await broadcast_to_board_subscribers(board_id, payload)

                await redis_client.xack("task:events", "group-websocket-broadcaster", message_id)



        except Exception:
            logger.exception("broadcast consumer failed")
            read_from = PENDING  # go back and retry whatever is still unacked
            await asyncio.sleep(1)