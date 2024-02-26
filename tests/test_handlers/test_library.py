from httpx import AsyncClient

test_book_name = 'Intermezzo'


async def test_book_search(test_client: AsyncClient):
    response = await test_client.get(f'/library/Intermezzo')
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert len(response.json()["data"]) == 1
