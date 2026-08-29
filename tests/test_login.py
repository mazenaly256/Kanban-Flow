import bcrypt
from starlette import status
from starlette.concurrency import run_in_threadpool

from app.models import User
from app.core.security import decode_jwt_access_token


async def test_successful_login_returns_200_and_login_response_schema(client, db_session):
    # Arrange
    mock_user_email = "dummyemail@example.com"
    mock_user_password = "dummy_password_for_testing"

    test_user = User(
        email=mock_user_email,
        username="test_user",
        hashed_password=(await run_in_threadpool(
            bcrypt.hashpw,
            mock_user_password.encode(),
            bcrypt.gensalt()
        )).decode()
    )

    db_session.add(test_user)
    await db_session.commit()



    # Act
    login_request_body = {
        "email": mock_user_email,
        "password": mock_user_password,
    }

    response = await client.post("/auth/login", json=login_request_body)
    response_body = response.json()     # converts JSON body into python dictionary


    # Assert
    assert response.status_code == status.HTTP_200_OK

    assert "access_token" in response_body and response_body["access_token"]
    assert ("token_type" in response_body) and (response_body["token_type"] == "bearer")


async def test_successful_login_returns_a_valid_jwt_token(client, db_session):
    # Arrange
    mock_user_email = "dummyemail@example.com"
    mock_user_password = "dummy_password_for_testing"

    mock_user = User(
        email=mock_user_email,
        username="test_user",
        hashed_password=(await run_in_threadpool(
            bcrypt.hashpw,
            mock_user_password.encode(),
            bcrypt.gensalt()
        )).decode()
    )

    db_session.add(mock_user)
    await db_session.commit()
    await db_session.refresh(mock_user)

    # Act
    login_request_body = {
        "email": mock_user_email,
        "password": mock_user_password,
    }

    response = await client.post("/auth/login", json=login_request_body)
    response_body = response.json()  # converts JSON body into python dictionary
    payload = decode_jwt_access_token(response_body["access_token"])

    # Assert
    assert payload is not None
    assert int(payload.get("sub")) == mock_user.id