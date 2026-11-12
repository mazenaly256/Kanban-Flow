import json

from app.websockets import broadcast_to_board_subscribers


async def websocket_broadcasting_consumer(redis_client):
    while True:

        # read messages in the 'task:events' stream for the websocket broadcaster consumer group
        streams_messages = await redis_client.xreadgroup(
            groupname="group-websocket-broadcaster",
            consumername="worker-1",
            streams={"task:events": ">"},
            count=5,
            block=2000
        )

        if streams_messages:
            for stream_name, messages in streams_messages:
                for message_id, data in messages:
                    board_id = int(data["board_id"])  # Values come back as strings from Redis
                    payload = json.loads(data["payload"])  # Parse JSON string back into a dict
                    await broadcast_to_board_subscribers(board_id, payload)

                    await redis_client.xack("task:events", "group-websocket-broadcaster", message_id)