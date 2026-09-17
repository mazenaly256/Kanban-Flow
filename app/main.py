import asyncio

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
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()  # server accepts to upgrade the connection to websockets (accepting the handshake and responding with HTTP 101)

    try:
        auth_message = await asyncio.wait_for(websocket.receive_text(), timeout=10)     # wait in the background, either text is received or the timeout is reached and throws asyncio.TimeoutError exception

    except asyncio.TimeoutError:
        await websocket.close(code=1008, reason="Authentication timeout")   # sends the last message, that is the closing of connection