import asyncio

import asyncpg
import pytest
from httpx import AsyncClient
from sqlalchemy import text, NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from typing import AsyncGenerator
import src.config as settings
from src.app.main import app
from fastapi.testclient import TestClient
from src.database import Base, get_async_session

TEST_DATABASE_URL = (f"postgresql+asyncpg://{settings.TEST_DB_USER}:{settings.TEST_DB_PASS}@{settings.TEST_DB_HOST}:"
                     f"{settings.TEST_DB_PORT}/{settings.TEST_DB_NAME}")

CLEAN_TABLES = [
    "public.user",
    "book"
]


@pytest.fixture(scope="session", autouse=True)
async def clean_tables():
    """
    Clean data in all tables before running test function
    WARNING!!! this function working only when tables in database already exists
    comment this function in other case
    """
    async with override_async_session_maker() as session:
        async with session.begin():
            for table_for_cleaning in CLEAN_TABLES:
                await session.execute(text(f"""TRUNCATE TABLE {table_for_cleaning} CASCADE;"""))


test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

override_async_session_maker = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False)
Base.metadata.bind = test_engine


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with override_async_session_maker() as session:
        yield session

app.dependency_overrides[get_async_session] = override_get_async_session


@pytest.fixture(scope="session")
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url='http://127.0.0.1') as ac:
        yield ac


@pytest.fixture(scope="session")
async def asyncpg_pool():
    pool = await asyncpg.create_pool(
        "".join(TEST_DATABASE_URL.split("+asyncpg"))
    )
    yield pool
    pool.close()


# @pytest.fixture(scope="session", autouse=True)
# async def run_migrations():
#     os.system("alembic init migrations")
#     os.system('alembic revision --autogenerate -m "test running migrations"')
#     os.system("alembic upgrade head")


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://127.0.0.1") as ac:
        yield ac


@pytest.fixture(scope="session")
async def get_test_session():
    connection = await test_engine.connect()
    transaction = await connection.begin()
    override_async_session_maker.configure(bind=connection)

    async with override_async_session_maker() as session:
        yield session

    await transaction.rollback()
    await connection.close()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


client = TestClient(app)
link = 'http://127.0.0.1:8000'

