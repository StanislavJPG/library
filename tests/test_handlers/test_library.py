import asyncio

from httpx import AsyncClient
from sqlalchemy import text

from src.library.router import get_read_page_api, save_book_page_api
from src.library.service import save_book_database
from tests.conftest import link, override_async_session_maker, test_client

test_book_name = 'ревізор'


async def test_book_search(test_client: AsyncClient):
    response = await test_client.get(f'{link}/api/library/{test_book_name}')
    assert response.status_code == 200

book_num = 1


async def test_create_temp_book(test_client: AsyncClient):
    response = await test_client.post(f'{link}/api/library/books/let_find', json={
        "title": f"{test_book_name}",
        "image": "string",
        "description": "string",
        "url": "string",
        "url_orig": "string"
    })

    assert response.status_code == 200


class TestUser:
    def __init__(self, test_client: AsyncClient):
        self.test_client = test_client
        self._id = None

    @property
    def id(self):
        if self._id is None:
            raise ValueError("User ID not set")
        return self._id

    async def fetch_id(self):
        registration = await self.test_client.post(f'{link}/auth/register', json={
            "email": "user@example.com",
            "password": "strings123",
            "is_active": True,
            "is_superuser": False,
            "is_verified": False,
            "username": "String"
        })
        if registration.status_code == 201:
            async with override_async_session_maker() as session:
                stmt = await session.scalar(
                    text(f"""SELECT public.user.id FROM public.user WHERE public.user.username = 'String'"""))
                self._id = stmt


async def test_read(test_client: AsyncClient, get_test_session):
    # user = TestUser(test_client)
    # await user.fetch_id()
    # await get_read_page_api(literature=test_book_name, num=book_num, user=user, session=get_test_session)
    response = await test_client.get(f'{link}/api/library/read/ревізор?num=1')
    assert response.status_code == 200


# async def test_save_book(test_client: AsyncClient, get_test_session):
#     user = TestUser(test_client)
#     await user.fetch_id()
#     await save_book_page_api(literature=test_book_name, num=book_num, user=user, session=get_test_session)
#     # await save_book_database(book=test_book_name, num=book_num, user=user, session=get_test_session)

