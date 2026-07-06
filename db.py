import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base


USER = os.environ.get("DB_USER")
PASSWORD = os.environ.get("DB_PASSWORD")
HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
PORT = os.environ.get("DB_PORT")



# FOR LOCAL TESTING ------------------------------------------------------------------------------------
HOST_DEV = os.getenv("DB_HOST_DEV")
DATABASE_URL = os.getenv("URL", f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST_DEV}:{PORT}/{DB_NAME}")
# ------------------------------------------------------------------------------------------------------
#DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

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