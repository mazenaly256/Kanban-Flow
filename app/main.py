import asyncio
import json
from app.core.security import decode_jwt_access_token

from fastapi import FastAPI
from starlette.websockets import WebSocket

from app.routers import health, auth, users, boards, board_columns, tasks

app = FastAPI()

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(boards.router)
app.include_router(board_columns.router)
app.include_router(tasks.router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):     # executed once per connection
    await websocket.accept()  # server accepts to upgrade the connection to websockets (accepting the handshake and responding with HTTP 101)

    try:
        message = await asyncio.wait_for(websocket.receive_text(), timeout=10)     # wait in the background, either text is received or the timeout is reached and throws asyncio.TimeoutError exception

        data = json.loads(message)
        jwt = data.get("token")

        user = decode_jwt_access_token(jwt)

        if user is None:
            await websocket.close(code=1008, reason="Invalid token")    # '.close()' sends the closing message/frame to the client

    except asyncio.TimeoutError:
        await websocket.close(code=1008, reason="Authentication timeout")   # sends the last message, that is the closing of connection