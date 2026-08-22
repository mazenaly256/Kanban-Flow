import pytest
from starlette import status


@pytest.mark.asyncio
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