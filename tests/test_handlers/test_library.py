from httpx import AsyncClient
from sqlalchemy import text

from src.library.service import BookConnection
from tests.conftest import link, override_async_session_maker, override_get_async_session

test_book_name = 'ревізор'


async def test_book_search(test_client: AsyncClient):
    response = await test_client.get(f'{link}/api/library/{test_book_name}')
    assert response.status_code == 200

book_num = 1


async def test_read(test_client: AsyncClient):
    response = await test_client.get(f'{link}/api/library/read/{test_book_name}?num={book_num}')
    assert response.status_code == 200


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

    @property
    async def id(self):
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
        return stmt


async def test_save_book(test_client: AsyncClient):
    user = TestUser(test_client)

    _database_conn = BookConnection(book=test_book_name, num=book_num, user=user)
    await _database_conn.save_book_db(session=override_async_session_maker())
