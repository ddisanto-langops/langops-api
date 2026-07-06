import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base


USER = os.environ.get("DB_USER")
PASSWORD = os.environ.get("DB_PASSWORD")
HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
PORT = os.environ.get("DB_PORT")

ENV = os.getenv("ENVIRONMENT")
if ENV == 'PROD':
    DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
elif ENV == 'DEV':
    DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@localhost:{PORT}/{DB_NAME}"



engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    connect_args={"ssl": "disable"}
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