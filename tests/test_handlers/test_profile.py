import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.main import create_upload_file
from src.database import RedisCache
from src.profile.router import get_profile_api, delete_book_from_profile_api, save_book_back_to_profile_api
from tests.conftest import link
from tests.test_handlers.conftest import override_get_async_session, TestUser, test_book_name


@pytest.mark.asyncio
async def test_profile(test_client: AsyncClient, override_get_async_session: AsyncSession):
    user = TestUser(test_client)
    await user.fetch_id(is_saved_to_profile=True)
    test_profile_info = await get_profile_api(session=override_get_async_session, book_name=test_book_name,
                                              page=1, user=user)

    is_profile_data_in_redis = await RedisCache().get_alike('books_pagination_in_profile')
    assert is_profile_data_in_redis is not None
    assert isinstance(is_profile_data_in_redis, list)
    assert test_profile_info is not None
    assert isinstance(test_profile_info, dict)


async def test_unauthorized_profile(test_client: AsyncClient):
    response = await test_client.get(f'{link}/api/profile')
    assert response.status_code == 401


async def test_delete_book_from_profile(test_client: AsyncClient, override_get_async_session: AsyncSession):
    user = TestUser(test_client)
    await user.fetch_id(is_saved_to_profile=False)
    book_id = await user.book_id
    response = await delete_book_from_profile_api(book_id=book_id, session=override_get_async_session, user=user)
    assert response is None


async def test_save_book_back_to_profile(test_client: AsyncClient, override_get_async_session: AsyncSession):
    user = TestUser(test_client)
    await user.fetch_id(is_saved_to_profile=False)
    book_id = await user.book_id
    response = await save_book_back_to_profile_api(book_id=book_id, user=user, session=override_get_async_session)
    assert response is None
