import pytest
from httpx import AsyncClient

from src.library.service import save_book_database
from tests.conftest import link
from tests.test_handlers.conftest import override_get_async_session, TestUser

test_book_name = 'ромео і джульєтта'


async def test_book_search(test_client: AsyncClient):
    response = await test_client.get(f'{link}/api/library/{test_book_name}')
    assert response.text is not None
    assert response.status_code == 200

book_num = 1


async def test_read_book(test_client: AsyncClient):
    response = await test_client.get(f'{link}/api/library/read', params={
        "literature": test_book_name,
        "num": book_num
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_temp_book(test_client: AsyncClient):
    response = await test_client.post(f'{link}/api/library/books/let_find', json={
        "title": f"{test_book_name}",
        "image": "string",
        "description": "string",
        "url": "string",
        "url_orig": "string"
    })

    assert response.status_code == 200


async def test_save_book(test_client: AsyncClient, override_get_async_session):
    user = TestUser(test_client)
    await user.fetch_id(is_saved_to_profile=True)
    response = await save_book_database(book=test_book_name, num=1,
                                        session=override_get_async_session, user=user, rating=4)
    assert response is None
