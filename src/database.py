import json
import aioredis
from typing import AsyncGenerator, Union, Any

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

from src.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER


DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base = declarative_base()


class User(SQLAlchemyBaseUserTableUUID, Base):
    username: Mapped[str] = mapped_column(String)
    profile_image: Mapped[str] = mapped_column(String)


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


class RedisCash:
    """
    This class provides data cash logic with aioredis (async redis)
    """

    REDIS = aioredis.from_url('redis://localhost')

    def __init__(self, value: str):
        self.value_name = value

    async def check(self) -> Union[True, None]:
        cached_data = await self.REDIS.get(self.value_name)
        if cached_data:
            return True
        await self.REDIS.close()

    async def get(self) -> dict:
        cached_data = await self.REDIS.get(self.value_name)
        data = json.loads(cached_data)
        await self.REDIS.close()

        return data

    async def executor(self, data: Any, ex: int = None) -> Any:
        cached_data = await self.REDIS.get(self.value_name)
        if cached_data:
            data = json.loads(cached_data)
            return data

        serialized_data = json.dumps(data)
        # ex = None is permanent key in redis
        await self.REDIS.set(name=self.value_name, value=serialized_data, ex=ex)
        await self.REDIS.close()

        return data

    async def delete(self) -> None:
        await self.REDIS.delete(self.value_name)
