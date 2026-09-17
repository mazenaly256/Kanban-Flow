import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app

client = TestClient(app)        # httpx.AsyncClient can not communicate with websockets protocol (handshake + sending messages)

def test_ws_closes_when_no_jwt_sent_before_authentication_timeout():
    with client.websocket_connect("/ws") as ws:     # 'with' is used to clean up resources including closing the websockets connection
        with pytest.raises(WebSocketDisconnect) as exc_info:    # this is an assertion that an exception of type 'WebSocketDisconnect' is thrown
            ws.receive_text()   # Block here until the server sends a text message (data message), exception is thrown after the timeout as the client only receives control message/frame that is closing the connection

    assert exc_info.value.code == 1008      # the control message that is received on closing the connection has closing code 1008, that means policy violation (not sending the jwt before authentication timeout)