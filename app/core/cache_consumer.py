from app.core.cache import cache_board_delete


async def cache_invalidation_consumer(redis_client):
    while True:

        # read messages in the 'task:events' stream for the cache invalidator consumer group
        streams_messages = await redis_client.xreadgroup(
            groupname="group-cache-invalidator",
            consumername="worker-1",
            streams={"task:events": ">"},
            count=5,
            block=2000
        )

        if streams_messages:
            for stream_name, messages in streams_messages:  # unpacks outer tuple
                for message_id, data in messages:   # unpacks inner tuple
                    board_id = int(data["board_id"])
                    await cache_board_delete(redis_client, board_id)
                    await redis_client.xack("task:events", "group-cache-invalidator", message_id)