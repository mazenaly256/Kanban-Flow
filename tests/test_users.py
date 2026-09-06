import bcrypt
from starlette import status

from app.models import User
from starlette.concurrency import run_in_threadpool
from app.core.security import issue_jwt_access_token



async def test_valid_token_returns_200_with_user_read_schema(client, db_session):
    # Arrange
    test_user = User(  # insert user directly into DB to avoid testing register functionality in this test
        email="dummyemail@example.com",
        username="test_user",
        hashed_password=(await run_in_threadpool(
            bcrypt.hashpw,
            "dummy_password".encode(),
            bcrypt.gensalt()
        )).decode()
    )

    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    access_token = issue_jwt_access_token(test_user.id)   # to only test with valid token, and the errors in register or login do not propagate here


    # Act
    response = await client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    response_body = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert "hashed_password" not in response_body and "id" in response_body and "email" in response_body and "username" in response_body



async def test_invalid_token_returns_401(client):
    # Act
    response = await client.get("/users/me", headers={"Authorization": "Bearer Dummy.Invalid.Token"})


    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED



async def test_missing_authorization_header_returns_401(client):
    # Act
    response = await client.get("/users/me")


    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED