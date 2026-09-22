from starlette.websockets import WebSocket


class BoardSubscriptionManager:
    def __init__(self):
        # maps subscribed connections to a specific board, user_id is not concerned
        self._subscribed_connections: dict[int, set[WebSocket]] = {}  # set is used for fast removal, as order is not important here


    def subscribe(self, board_id: int, ws: WebSocket):
        if board_id not in self._subscribed_connections:   # checks if board id is a key in the dictionary
            self._subscribed_connections[board_id] = set()

        self._subscribed_connections[board_id].add(ws)


    def unsubscribe(self, board_id: int, ws: WebSocket):
        if board_id in self._subscribed_connections:
            self._subscribed_connections[board_id].discard(ws)

            if not self._subscribed_connections[board_id]:      # if the set is empty
                del self._subscribed_connections[board_id]      # then delete the key and value from the memory to clean up


    def get_all_subscribed_connections(self, board_id: int) -> set[WebSocket] | None:
        if board_id in self._subscribed_connections:
            return self._subscribed_connections[board_id]

        else:
            return None



board_subscription_manager = BoardSubscriptionManager()