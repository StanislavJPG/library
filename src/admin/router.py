from typing import Optional, Union

from src.admin.service import AdminPanel
from src.auth.base_config import current_superuser
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from src.database import async_session_maker, RedisCash
from src.library.models import Book
from src.library.shemas import BookCreate


router = APIRouter(
    prefix='/api/admin_panel',
    tags=['admin_panel']
)


@router.post('/create_book', response_model=None)
async def create_book_api(book: BookCreate, page: int):
    async with async_session_maker() as session:

        books_request_instance = await AdminPanel(page).get_users_requests()
        query_book_as_dict = [book.as_dict()['title'] for book in books_request_instance]

        is_book_exists = await session.scalar(select(Book).where(
            (Book.title.in_(query_book_as_dict)) & (Book.id == int(book.id))
        )) is not None

        if is_book_exists:
            await session.execute(update(Book).values(
                title=book.title,
                description=book.description,
                url=book.url,
                url_orig=book.url_orig
            ).where((Book.title.in_(query_book_as_dict)) & (Book.id == int(book.id))))
            await session.commit()
        else:
            raise HTTPException(status_code=400)


@router.get('/', response_class=HTMLResponse, dependencies=[Depends(current_superuser)])
async def admin_panel_api(page: Optional[int] = 1):
    redis = RedisCash('admin_panel')
    is_cache_exists = await redis.check()

    if is_cache_exists:
        books_request = await redis.get()
    else:
        admin_panel_instance = await AdminPanel(page).get_users_requests()
        books_request = await redis.executor(data=[el.as_dict() for el in admin_panel_instance],
                                             ex=10)
    return {'books_request': books_request, 'page': page}
