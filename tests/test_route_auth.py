import pytest
from unittest.mock import MagicMock, AsyncMock, ANY
from sqlalchemy import select
from fastapi.security import HTTPAuthorizationCredentials

from src.database.models import User
from src.schemas import RequestEmail
from src.services.auth import auth_service

@pytest.mark.asyncio
async def test_create_user(client, user, monkeypatch):
    # Подменяем send_email, чтобы не отправлялось реально
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    response = await client.post("/api/auth/signup", json=user)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["email"] == user["email"]
    assert "id" in data["user"]
    mock_send_email.assert_called_once()


@pytest.mark.asyncio
async def test_repeat_create_user(client, user):
    response = await client.post("/api/auth/signup", json=user)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"


@pytest.mark.asyncio
async def test_login_user_not_confirmed(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')}
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"


@pytest.mark.asyncio
async def test_login_user(client, session, user):
    # Подтверждаем пользователя
    result = await session.execute(select(User).filter_by(email=user["email"]))
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    session.add(db_user)
    await session.commit()

    response = await client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": 'wrongpass'}
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"


@pytest.mark.asyncio
async def test_login_wrong_email(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": 'wrong@email.com', "password": user.get('password')}
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


@pytest.mark.asyncio
async def test_refresh_token_success(client, user, monkeypatch, session):
    # Мокаем decode_refresh_token, чтобы возвращал email
    monkeypatch.setattr(
        "src.services.auth.auth_service.decode_refresh_token",
        AsyncMock(return_value=user["email"])
    )

    # Мокаем update_token, чтобы просто пропускал вызов
    monkeypatch.setattr(
        "src.repository.users.update_token",
        AsyncMock(return_value=None)
    )

    # Создаем объект пользователя с токеном
    from src.database.models import User
    result = await session.execute(select(User).filter_by(email=user["email"]))
    current_user = result.scalar_one()
    current_user.refresh_token = "refresh_token_value"
    session.add(current_user)
    await session.commit()

    # Передаем credentials в Security
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="refresh_token_value")

    # Вызов эндпоинта напрямую через маршрутизатор
    from src.routes import auth
    response = await auth.refresh_token(credentials=credentials, db=session)

    assert "access_token" in response
    assert "refresh_token" in response
    assert response["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_confirmed_email_first_time(client, user, monkeypatch, session):
    # Мокаем get_email_from_token
    monkeypatch.setattr(
        "src.services.auth.auth_service.get_email_from_token",
        AsyncMock(return_value=user["email"])
    )

    # Мокаем confirmed_email
    monkeypatch.setattr(
        "src.repository.users.confirmed_email",
        AsyncMock(return_value=None)
    )

    # Устанавливаем confirmed=False
    result = await session.execute(select(User).filter_by(email=user["email"]))
    current_user = result.scalar_one()
    current_user.confirmed = False
    session.add(current_user)
    await session.commit()

    from src.routes import auth
    response = await auth.confirmed_email(token="fake_token", db=session)
    assert response["message"] == "Email confirmed"

@pytest.mark.asyncio
async def test_confirmed_email_already_confirmed(client, user, monkeypatch, session):
    # Мокаем get_email_from_token
    monkeypatch.setattr(
        "src.services.auth.auth_service.get_email_from_token",
        AsyncMock(return_value=user["email"])
    )

    # Установим confirmed = True в базе
    from src.database.models import User
    result = await session.execute(select(User).filter_by(email=user["email"]))
    current_user = result.scalar_one()
    current_user.confirmed = True
    session.add(current_user)
    await session.commit()

    from src.routes import auth
    response = await auth.confirmed_email(token="fake_token", db=session)
    assert response["message"] == "Your email is already confirmed"


@pytest.mark.asyncio
async def test_request_email_already_confirmed(client, session, user):
    # Пользователь подтвержден
    result = await session.execute(select(User).filter_by(email=user["email"]))
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    session.add(db_user)
    await session.commit()

    response = await client.post("/api/auth/request_email", json={"email": user["email"]})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Your email is already confirmed"

