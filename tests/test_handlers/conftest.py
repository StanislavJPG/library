from typing import Union, AsyncGenerator
import pytest
from httpx import AsyncClient
from sqlalchemy import text, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import User
from src.library.models import Library, Book
from tests.conftest import async_session_maker

test_book_name = 'ромео і джульєтта'
book_num = 1


@pytest.fixture(scope='function')
async def override_get_async_session() -> Union[AsyncGenerator[AsyncSession, None], AsyncSession]:
    async with async_session_maker() as session:
        yield session


class TestUser:
    __test__ = False

    def __init__(self, test_client: AsyncClient):
        self.test_client = test_client
        self._id = None

    @property
    def id(self):
        if self._id is None:
            raise NotImplemented
        return self._id

    @property
    async def book_id(self):
        async with async_session_maker() as session:
            async with session.begin():
                book_id = await session.scalar(select(Book.id))
                return book_id

    async def fetch_id(self, is_saved_to_profile: bool, rating: int = None):
        async with async_session_maker() as session:
            async with session.begin():
                user_id = await session.scalar(select(User.id).where(User.username == 'String'))
                book_id = await self.book_id
                await session.scalar(insert(Library).values(user_id=user_id, book_id=book_id,
                                                            rating=rating, is_saved_to_profile=is_saved_to_profile))
                await session.commit()
            self._id = user_id
