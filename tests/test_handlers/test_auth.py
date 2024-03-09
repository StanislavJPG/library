import pytest
from httpx import AsyncClient

from tests.conftest import link


@pytest.mark.dependency()
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


async def test_bad_registration(test_client: AsyncClient):
    response_reg = await test_client.post(f'{link}/auth/register', json={
        "email": "bad_user",
        "password": 123,
        "is_active": True,
        "is_superuser": False,
        "is_verified": False,
        "username": 123
    })
    assert response_reg.status_code == 422


@pytest.mark.dependency(depends=["test_registration"])
async def test_login(test_client: AsyncClient):
    response_log = await test_client.post(f'{link}/auth/jwt/login', data={
            "username": "user@example.com",
            "password": "strings123",
        })
    assert response_log.status_code == 204


@pytest.mark.dependency(depends=["test_registration"])
async def test_bad_login(test_client: AsyncClient):
    response_log = await test_client.post(f'{link}/auth/jwt/login', data={
        "username": "bad_user@example.com",
        "password": "strings123",
    })
    assert response_log.status_code == 400
