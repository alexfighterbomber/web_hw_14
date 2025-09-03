import pytest
from unittest.mock import MagicMock, patch
from jose import jwt
from fastapi import HTTPException, status

from src.services.auth import auth_service, Auth
from src.database.models import User

SECRET_KEY = auth_service.SECRET_KEY
ALGORITHM = auth_service.ALGORITHM


@pytest.mark.asyncio
async def test_password_hash_and_verify():
    password = "mypassword"
    hashed = auth_service.get_password_hash(password)
    assert auth_service.verify_password(password, hashed)
    assert not auth_service.verify_password("wrong", hashed)


@pytest.mark.asyncio
async def test_create_and_decode_access_token():
    data = {"sub": "test@example.com"}
    token = await auth_service.create_access_token(data, expires_delta=60)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "test@example.com"
    assert payload["scope"] == "access_token"


@pytest.mark.asyncio
async def test_create_and_decode_refresh_token():
    data = {"sub": "test@example.com"}
    token = await auth_service.create_refresh_token(data, expires_delta=60)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "test@example.com"
    assert payload["scope"] == "refresh_token"


@pytest.mark.asyncio
async def test_decode_refresh_token_success():
    token = await auth_service.create_refresh_token({"sub": "test@example.com"})
    email = await auth_service.decode_refresh_token(token)
    assert email == "test@example.com"


@pytest.mark.asyncio
async def test_decode_refresh_token_invalid_scope():
    from jose import jwt
    token = jwt.encode({"sub": "test@example.com", "scope": "access_token"}, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.decode_refresh_token(token)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_email_from_token_success():
    token = auth_service.create_email_token({"sub": "test@example.com"})
    email = await auth_service.get_email_from_token(token)
    assert email == "test@example.com"


@pytest.mark.asyncio
async def test_get_email_from_token_invalid():
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.get_email_from_token("invalid.token")
    assert excinfo.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_current_user_from_db():
    # Создаём "живого" пользователя
    fake_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password="hashed",
        confirmed=True,
        avatar=None
    )

    async def fake_get_user_by_email(email, db):
        return fake_user

    with patch("src.services.auth.repository_users.get_user_by_email", new=fake_get_user_by_email):
        token = await auth_service.create_access_token({"sub": "test@example.com"})
        user = await auth_service.get_current_user(token=token, db=None)
        assert user.email == "test@example.com"
        assert user.username == "testuser"