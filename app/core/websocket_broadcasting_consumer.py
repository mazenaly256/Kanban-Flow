def websocket_broadcasting_consumer(redis_client):
    while True:

        # read messages in the 'task:events' stream for the websocket broadcaster consumer group
        streams_messages = redis_client.xreadgroup(
            groupname="group-websocket-broadcaster",
            consumername="worker-1",
            streams={"task:events": ">"},
            count=5,
            block=2000
        )

        if streams_messages:
            for stream_name, messages in streams_messages:
                for message_id, data in messages:
                    redis_client.xack("task:events", "group-websocket-broadcaster", message_id)