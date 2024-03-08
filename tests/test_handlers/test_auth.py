from httpx import AsyncClient

from tests.conftest import link


async def test_registration(test_client: AsyncClient):
    response_reg = await test_client.post(f'{link}/auth/register', json={
        "email": "user@example.com",
        "password": "strings123",
        "is_active": True,
        "is_superuser": False,
        "is_verified": False,
        "username": "String"
    })
    assert response_reg.status_code == 201
