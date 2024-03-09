import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.router import create_book_api, search_specific_book_from_database_api, admin_panel_api
from src.database import RedisCache
from src.library.shemas import BookCreate
from tests.test_handlers.conftest import override_get_async_session, TestUser, test_book_name
from tests.test_handlers.test_service import test_create_temp_book


@pytest.mark.dependency(depends=["test_create_temp_book"])
async def test_create_book(test_client: AsyncClient, override_get_async_session: AsyncSession):
    user = TestUser(test_client)
    book_id = await user.book_id
    data = {
        "id": book_id,
        "title": f'«{test_book_name}»',
        "image": "test_image",
        "description": "test_desc",
        "url": "test_url",
        "url_orig": "test_url_orig"
    }
    book_schema = BookCreate(**data)
    response = await create_book_api(book=book_schema, session=override_get_async_session)
    assert response is None


async def test_search_specific_book_from_database(test_client: AsyncClient, override_get_async_session: AsyncSession):
    response = await search_specific_book_from_database_api(book_title=test_book_name,
                                                            session=override_get_async_session)
    assert response.as_dict()['title'] == f'«{test_book_name}»'


async def test_admin_panel(override_get_async_session: AsyncSession):
    await admin_panel_api(session=override_get_async_session)
    is_admin_panel_data_in_redis = await RedisCache("admin_panel").check()
    assert is_admin_panel_data_in_redis
