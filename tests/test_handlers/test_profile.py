import pytest
from httpx import AsyncClient

from src.profile.router import get_profile_api
from tests.conftest import link
from tests.test_handlers.test_service import test_book_name, test_create_temp_book
from tests.test_handlers.conftest import override_get_async_session, TestUser


@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_create_temp_book"])
async def test_profile(test_client: AsyncClient, override_get_async_session):
    user = TestUser(test_client)
    await user.fetch_id(is_saved_to_profile=True)
    test_profile_info = await get_profile_api(session=override_get_async_session, book_name=test_book_name,
                                              page=1, user=user)
    assert test_profile_info is not None
    assert isinstance(test_profile_info, dict)


async def test_unauthorized_profile(test_client: AsyncClient):
    response = await test_client.get(f'{link}/api/profile')
    assert response.status_code == 401
