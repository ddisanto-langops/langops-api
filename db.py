import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

URL = os.environ.get("DB_URL")
USER = os.environ.get("DB_USER")
PASSWORD = os.environ.get("DB_PASSWORD")
HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
PORT = os.environ.get("DB_PORT")
ID = os.environ.get("CF_CLIENT_ID")
SECRET = os.environ.get("CF_CLIENT_SECRET")

DATABASE_URL = os.getenv("URL", f"postgresql+asyncpg://{USER}:{PASSWORD}@localhost:{PORT}/{DB_NAME}")


engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    connect_args={"ssl": "disable"}  # Set to "require" if SSL is managed at the PG instance level
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()