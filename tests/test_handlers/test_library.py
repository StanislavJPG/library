
from httpx import AsyncClient

from tests.conftest import link

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


async def test_read_book(test_client: AsyncClient):
    response = await test_client.get(f'{link}/api/library/read', params={
        "literature": test_book_name,
        "num": book_num
    })
    assert response.status_code == 200
