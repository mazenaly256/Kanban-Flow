from starlette import status


async def test_register_with_valid_data_returns_201(client):
    request_body = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
        "password_confirmation": "password123",
    }

    response = await client.post("/auth/register", json=request_body)

    assert response.status_code == status.HTTP_201_CREATED

    body = response.json()
    assert body["email"] == request_body["email"]
    assert body["username"] == request_body["username"]
    assert "hashed_password" not in body
    assert "id" in body


async def test_unmatched_password_returns_422(client):
    request_body = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
        "password_confirmation": "123password",
    }

    response = await client.post("/auth/register", json=request_body)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_username_already_exists_returns_409(client):
    request_body = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
        "password_confirmation": "password123",
    }

    response = await client.post("/auth/register", json=request_body)

    assert response.status_code == status.HTTP_201_CREATED

    request_body = {
        "email": "test2@example.com",
        "username": "testuser",
        "password": "password123",
        "password_confirmation": "password123",
    }

    response = await client.post("/auth/register", json=request_body)

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_email_already_exists_returns_409(client):
    request_body = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
        "password_confirmation": "password123",
    }

    response = await client.post("/auth/register", json=request_body)

    assert response.status_code == status.HTTP_201_CREATED

    request_body = {
        "email": "test@example.com",
        "username": "testuser2",
        "password": "password123",
        "password_confirmation": "password123",
    }

    response = await client.post("/auth/register", json=request_body)

    assert response.status_code == status.HTTP_409_CONFLICT