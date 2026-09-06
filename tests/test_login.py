import bcrypt
import pytest
from starlette import status
from starlette.concurrency import run_in_threadpool

from app.models import User
from app.core.security import decode_jwt_access_token


async def test_successful_login_returns_200_and_login_response_schema(client, db_session):
    # Arrange
    mock_user_email = "dummyemail@example.com"
    mock_user_password = "dummy_password_for_testing"

    test_user = User(   # insert user directly into DB to avoid testing register functionality in this test
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


@pytest.mark.parametrize(
    "login_request_body",
    [
        {"email": "invalidemail", "password": "any dummy password"},    # invalid email format
        {"email": "dummyemail@example.com"},                            # missing password
        {"password": "any dummy password"}                              # missing email
    ],
    ids=["invalid email format", "missing password field", "missing email"]
)
async def test_invalid_request_returns_422(client, db_session, login_request_body):
    # Act
    response = await client.post("/auth/login", json=login_request_body)


    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_email_does_not_exist_returns_401(client, db_session):
    # Arrange
    login_request_body = {
        "email": "anyinexistentvalidemail@example.com",
        "password": "any dummy_password",
    }

    # Act
    response = await client.post("/auth/login", json=login_request_body)
    response_body = response.json()  # converts JSON body into python dictionary

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_wrong_password_returns_401(client, db_session):
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
        "password": "Wrong Password"
    }

    response = await client.post("/auth/login", json=login_request_body)
    response_body = response.json()  # converts JSON body into python dictionary


    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
