import os
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text
from typing import AsyncGenerator

import src.config as settings
from src.app.main import app
from fastapi.testclient import TestClient

from src.database import Base, get_async_session, RedisCash

CLEAN_TABLES = [
    "user",
]

TEST_DATABASE_URL = (f"postgresql+asyncpg://{settings.TEST_DB_USER}:{settings.TEST_DB_PASS}@{settings.TEST_DB_HOST}:"
                     f"{settings.TEST_DB_PORT}/{settings.TEST_DB_NAME}")


@pytest.fixture(scope="session", autouse=True)
async def clean_tables():
    """
    Clean data in all tables before running test function
    WARNING!!! this function working only when tables in database already exists
    comment this function in other case
    """
    async with test_async_session_maker() as session:
        async with session.begin():
            for table_for_cleaning in CLEAN_TABLES:
                stmt = text(f"TRUNCATE TABLE public.{table_for_cleaning} CASCADE;")
            await session.execute(stmt)
            await session.commit()


# @pytest.fixture(scope="session", autouse=True)
# async def run_migrations():
#     os.system("alembic init migrations")
#     os.system('alembic revision --autogenerate -m "test running migrations"')
#     os.system("alembic upgrade heads")


engine = create_async_engine(TEST_DATABASE_URL)
test_async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)
Base.metadata.bind = engine

client = TestClient(app)


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_async_session_maker() as session:
        yield session

app.dependency_overrides[get_async_session] = override_get_async_session


@pytest.fixture
async def redis_cash():
    """
    Fixture to create an instance of RedisCash for testing.
    """
    value_name = 'test_key'  # Provide a test key name
    redis_cash_instance = RedisCash(value_name)
    yield redis_cash_instance
    # Clean up after the test
    await redis_cash_instance.delete()


@pytest.fixture(scope="session")
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app) as ac:
        yield ac
