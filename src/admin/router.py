from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.service import AdminPanel
from src.auth.base_config import current_superuser
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, HTTPException

from src.crud import read_is_book_exists_by_request, update_book_args_by_admin
from src.database import RedisCash, get_async_session
from src.library.shemas import BookCreate


router = APIRouter(
    prefix='/api/admin_panel',
    tags=['admin_panel']
)


@router.post('/create_book', response_model=None)
async def create_book_api(book: BookCreate, page: int, session: AsyncSession = Depends(get_async_session)):
    """
    This is function made for managing book
    that users wants to add to the cite
    """
    query_book_as_dict = [book.as_dict()['title'] for book in await AdminPanel(page).get_users_requests(session)]

    if await read_is_book_exists_by_request(session=session, book=book, query=query_book_as_dict):
        await update_book_args_by_admin(session=session, book=book, query=query_book_as_dict)
    else:
        raise HTTPException(status_code=400)


@router.get('/', response_class=HTMLResponse, dependencies=[Depends(current_superuser)])
async def admin_panel_api(page: Optional[int] = 1, session: AsyncSession = Depends(get_async_session)):
    redis = RedisCash('admin_panel')
    is_cache_exists = await redis.check()

    if is_cache_exists:
        books_request = await redis.get()
    else:
        admin_panel_instance = await AdminPanel(page).get_users_requests(session=session)
        books_request = await redis.executor(data=[el.as_dict() for el in admin_panel_instance],
                                             ex=10)
    return {'books_request': books_request, 'page': page}
