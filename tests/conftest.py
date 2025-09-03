import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from main import app
from src.database.models import Base
from src.database.db import get_db
from src.database.models import User
from src.services.auth import auth_service


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, future=True)

TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest_asyncio.fixture(scope="module")
async def session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as db:
        yield db


@pytest_asyncio.fixture(scope="module")
async def client(session):
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="module")
def user():
    return {
        "username": "deadpool",
        "email": "deadpool@example.com",
        "password": "123456789"
    }

@pytest.fixture
async def logged_in_client(client, user, session):
    from src.database.models import User
    from sqlalchemy import select

    result = await session.execute(select(User).filter_by(email=user["email"]))
    existing_user = result.scalar_one_or_none()

    if not existing_user:
        new_user = User(
            email=user["email"],
            username=user["username"],
            password=auth_service.get_password_hash(user["password"]),
            confirmed=True
        )
        session.add(new_user)
        await session.commit()
 
    # 2. Логинимся
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": user["email"], "password": user["password"]}
    )
    token = login_resp.json()["access_token"]

    # 3. Класс для удобного использования клиента с токеном
    class ClientWithAuth:
        def __init__(self, client, token):
            self.client = client
            self.headers = {"Authorization": f"Bearer {token}"}

        async def get(self, url, **kwargs):
            kwargs.setdefault("headers", self.headers)
            return await self.client.get(url, **kwargs)

        async def post(self, url, **kwargs):
            kwargs.setdefault("headers", self.headers)
            return await self.client.post(url, **kwargs)

        async def put(self, url, **kwargs):
            kwargs.setdefault("headers", self.headers)
            return await self.client.put(url, **kwargs)

        async def delete(self, url, **kwargs):
            kwargs.setdefault("headers", self.headers)
            return await self.client.delete(url, **kwargs)
        
        async def patch(self, url, **kwargs): 
            kwargs.setdefault("headers", self.headers)
            return await self.client.patch(url, **kwargs)

    return ClientWithAuth(client, token)

