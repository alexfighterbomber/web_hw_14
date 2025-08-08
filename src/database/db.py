from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.conf.config import settings

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.conf.config import settings

# URL должен содержать async драйвер (postgresql+asyncpg, mysql+aiomysql и т. д.)
SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

# Асинхронный движок
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

# Асинхронная сессия
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Асинхронная зависимость для FastAPI
async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()  # Важно: закрытие сессии тоже асинхронное!