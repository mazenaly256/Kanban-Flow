from .board_subscription_manager import board_subscription_manager


async def broadcast_to_board_subscribers(board_id: int, message: dict):
    subscribed_websocket_connections = board_subscription_manager.get_all_subscribed_connections(board_id)

    for connection in subscribed_websocket_connections:
        try:
            await connection.send_json(message)

        except RuntimeError as ex:    # fires from sending messages via a closed connection
            # can happen when a disconnection occurs after fetching all connections
            print(f"Broadcast failed for a connection: {ex}")
