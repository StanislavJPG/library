import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

import src.config as settings


CLEAN_TABLES = [
    "user",
]

TEST_DATABASE_URL = (f"postgresql+asyncpg://{settings.TEST_DB_USER}:{settings.TEST_DB_PASS}@{settings.TEST_DB_HOST}:"
                     f"{settings.TEST_DB_PORT}/{settings.TEST_DB_NAME}")


@pytest.fixture(scope="session", autouse=True)
async def run_migrations():
    os.system("alembic init migrations")
    os.system('alembic revision --autogenerate -m "test running migrations"')
    os.system("alembic upgrade heads")


engine = create_async_engine(TEST_DATABASE_URL)
test_async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="function", autouse=True)
async def clean_tables():
    """Clean data in all tables before running test function"""
    async with test_async_session_maker() as session:
        async with session.begin():
            for table_for_cleaning in CLEAN_TABLES:
                stmt = text(f"TRUNCATE TABLE public.{table_for_cleaning} CASCADE")
                await session.execute(stmt)
