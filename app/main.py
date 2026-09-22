import asyncio
import json

from sqlalchemy import select

from app.core.security import decode_jwt_access_token
from app.core.database import AsyncSessionLocal

from fastapi import FastAPI
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.models import User, UserBoardRole
from app.routers import health, auth, users, boards, board_columns, tasks

from app.websockets import user_connections, board_subscription_manager

app = FastAPI()

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(boards.router)
app.include_router(board_columns.router)
app.include_router(tasks.router)


@app.websocket("/ws")
async def websocket_endpoint(websocket_connection: WebSocket):     # executed once per connection, and each call has its own variables and values isolated from other calls/connections
    await websocket_connection.accept()  # server accepts to upgrade the connection to websockets (accepting the handshake and responding with HTTP 101), once this line executed successfully, the client becomes connected

    try:
        message = await asyncio.wait_for(websocket_connection.receive_text(), timeout=10)     # wait in the background, either text is received or the timeout is reached and throws asyncio.TimeoutError exception

        data = json.loads(message)
        jwt = data.get("token")

        payload = decode_jwt_access_token(jwt)

        if payload is None:
            await websocket_connection.close(code=1008, reason="Invalid token")    # '.close()' sends the closing message/frame to the client
            return

        user_id = payload.get('sub')

        async with AsyncSessionLocal() as db:       # the db is not injected because this endpoint is executed once per the websocket connection, so the database session and connection will be reserved/held during the whole period of websocket connection
            result = await db.execute(select(User).where(User.id == int(user_id)))
            user_from_db = result.scalar_one_or_none()
        # session is automatically closed here (due to 'with') and database connection is returned to the pool

        await websocket_connection.send_json({"type": "successful_authentication"})     # acknowledgment of server that the user is now authenticated

        user_connections.add(user_id, websocket_connection)     # only the authenticated connections are what saved in memory


        try:
            while True:
                message = await websocket_connection.receive_text()     # pause the execution and wait till receive a message via this websocket connection, and throws exception if the connection is closed

                data = json.loads(message)
                message_type = data.get("type")

                if message_type == "subscribe" or message_type == "unsubscribe":
                    try:
                        board_id = int(data.get("board_id"))
                    except (ValueError, TypeError):
                        await websocket_connection.send_json(
                            {"type": "error", "message": "board_id must be given and must be a valid integer"})
                        continue

                    async with AsyncSessionLocal() as db:  # the db is not injected because this endpoint is executed once per the websocket connection, so the database session and connection will be reserved/held during the whole period of websocket connection
                        result = await db.execute(
                            select(UserBoardRole).where(UserBoardRole.board_id == board_id, UserBoardRole.user_id == int(user_id))
                        )

                        user_board_role = result.scalar_one_or_none()

                    if user_board_role is None:
                        await websocket_connection.send_json({
                            "type": "error",
                            "message": "User has no privileges to access the board"
                        })

                        continue

                    if message_type == "subscribe":
                        # it is required to firstly unsubscribe from the previous board id which the user was subscribed in
                        previous_subscription_board_id = getattr(websocket_connection.state, "board_id", None)
                        if previous_subscription_board_id is not None:
                            board_subscription_manager.unsubscribe(previous_subscription_board_id, websocket_connection)

                        board_subscription_manager.subscribe(board_id, websocket_connection)
                        websocket_connection.state.board_id = board_id
                        await websocket_connection.send_json({"type": "successful_board_subscription"})  # acknowledgment from server that the user is now subscribed in the board and will see live updates

                    else:
                        board_subscription_manager.unsubscribe(board_id, websocket_connection)
                        websocket_connection.state.board_id = None
                        await websocket_connection.send_json({"type": "successful_board_unsubscription"})


                else:
                    await websocket_connection.send_json({
                        "type": "error",
                        "message": "Message type is required" if message_type is None else f"Unsupported message type: {message_type}"
                    })



        except WebSocketDisconnect as closing_message:
            user_connections.remove(user_id, websocket_connection)

            # removing connection always implies removing a subscription to the board id that was subscribed to
            board_id = getattr(websocket_connection.state, "board_id", None)    # as the custom attribute may not be set
            if board_id is not None:
                board_subscription_manager.unsubscribe(board_id, websocket_connection)

            print(f"Client disconnected {closing_message.code} - {closing_message.reason}")


    except asyncio.TimeoutError:
        await websocket_connection.close(code=1008, reason="Authentication timeout")   # sends the last message, that is the closing of connection


    except WebSocketDisconnect as closing_message:      # enters here if the client disconnects while waiting for authenticating
        print(f"Client disconnected {closing_message.code} - {closing_message.reason}")