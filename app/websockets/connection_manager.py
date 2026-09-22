from starlette.websockets import WebSocket


class UserConnections:
    def __init__(self):
        # connections dictionary is defined here to map specific user_id with their connections
        self._connections: dict[int, set[WebSocket]] = {}  # set is used for fast removal, as order is not important here

    def add(self, user_id: int, ws: WebSocket):
        if user_id not in self._connections:   # checks if user id is a key in the dictionary
            self._connections[user_id] = set()

        self._connections[user_id].add(ws)


    def remove(self, user_id: int, ws: WebSocket):
        if user_id in self._connections:
            self._connections[user_id].discard(ws)

            if not self._connections[user_id]:      # if the set is empty
                del self._connections[user_id]      # then delete the key and value from the memory to clean up


    def get(self, user_id: int) -> set[WebSocket] | None:
        if user_id in self._connections:
            return self._connections[user_id]

        else:
            return None



user_connections = UserConnections()