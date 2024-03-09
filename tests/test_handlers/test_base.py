from httpx import AsyncClient

from tests.conftest import link


async def test_get_top_books(test_client: AsyncClient):
    response = await test_client.get(f'{link}/api/base/get_best_books')
    assert response.json()
    assert response.status_code == 200
