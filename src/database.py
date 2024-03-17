import json
from redis import asyncio as aioredis
from typing import AsyncGenerator, Union, Any

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

from src.config import (DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER, REDIS_HOST, REDIS_PORT)

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base = declarative_base()


class User(SQLAlchemyBaseUserTableUUID, Base):
    username: Mapped[str] = mapped_column(String)
    profile_image: Mapped[str] = mapped_column(String)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


class RedisCache:
    """
    This class provides data cache logic with aioredis (async redis)
    """
    REDIS = aioredis.from_url(f'redis://{REDIS_HOST}:{REDIS_PORT}')

    def __init__(self, value: str = None) -> None:
        self.value_name = value

    async def exist(self) -> Union[True, None]:
        """
        :return: True if cache for current data already exists or None if it's not
        """
        try:
            cached_data = await self.REDIS.get(self.value_name)
            if cached_data:
                return True
            await self.REDIS.close()
        finally:
            await self.REDIS.close()

    async def get(self) -> dict:
        """
        :return: dict with redis cache data
        """
        try:
            cached_data = await self.REDIS.get(self.value_name)
            data = json.loads(cached_data)
            await self.REDIS.close()
            return data
        finally:
            await self.REDIS.close()

    async def get_alike(self, *values) -> list:
        """
        This method aims to search keys that's looks like values args in redis
        """
        try:
            redis_keys = await self.REDIS.keys()
            alike_keys_list = []

            for key in redis_keys:
                for value in values:
                    if value in str(key)[2:-1]:
                        alike_keys_list.append(str(key)[2:-1])
            return alike_keys_list
        finally:
            await self.REDIS.close()

    async def executor(self, data: Any, ex: int = None) -> Any:
        try:
            cached_data = await self.REDIS.get(self.value_name)
            if cached_data:
                data = json.loads(cached_data)
                return data

            serialized_data = json.dumps(data)
            # ex = None is permanent key in Redis
            await self.REDIS.set(name=self.value_name, value=serialized_data, ex=ex)
            return data
        finally:
            await self.REDIS.close()

    async def delete(self, value: Any = None) -> None:
        try:
            if value:
                await self.REDIS.delete(value)
            else:
                await self.REDIS.delete(self.value_name)
        finally:
            await self.REDIS.close()
