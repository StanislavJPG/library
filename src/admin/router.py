from typing import Optional

from src.auth.base_config import current_superuser
from src.base.router import templates
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy import select, update, insert
from src.database import async_session_maker
from src.library.models import Book
from src.library.shemas import BookCreate


router = APIRouter(
    tags=['Admin Panel']
)


class AdminPanel:
    @staticmethod
    async def get_users_requests(page: int = 1):
        if page > 0:
            offset = (page - 1) * 4
        else:
            raise HTTPException(status_code=403, detail={'Error': 'Forbidden'})

        async with async_session_maker() as session:
            query = await session.scalars(select(Book).where(
                (Book.title.isnot(None)) & (Book.image.isnot(None)) &
                (Book.url_orig.is_(None))).offset(offset).limit(4)
            )
            books = query.all()
        return books

    @staticmethod
    @router.post('/admin_panel/create_book')
    async def create_book(book: BookCreate, page: int):
        async with async_session_maker() as session:
            query_books = await AdminPanel.get_users_requests(page)
            query_book = [book.as_dict()['title'] for book in query_books]

            is_book_exists = await session.scalar(select(Book).where(
                (Book.title.in_(query_book)) & (Book.id == int(book.id))
            )) is not None

            if is_book_exists:
                await session.execute(update(Book).values(
                    title=book.title,
                    description=book.description,
                    url=book.url,
                    url_orig=book.url_orig
                ).where((Book.title.in_(query_book)) & (Book.id == int(book.id))))
                await session.commit()
            else:
                raise HTTPException(status_code=400)

    @staticmethod
    @router.post('/books/let_find')
    async def create_temp_book(book: BookCreate):
        async with async_session_maker() as session:
            is_has_query_already = await session.scalar(select(Book).where(
                Book.title == f'«{book.title}»'
            ))  # user can make query to find book only if that book NOT in database already

            if is_has_query_already is None:
                await session.execute(insert(Book).values(
                    title=f'«{book.title}»',
                    image=book.image,
                    description=book.description
                ))
                await session.commit()
            else:
                raise HTTPException(status_code=409)


@router.get('/admin_panel')
async def admin_panel(request: Request, admin=Depends(current_superuser),
                      page: Optional[int] = 1):
    books_request = await AdminPanel.get_users_requests(page)

    return templates.TemplateResponse(
        'admin.html',
        {'request': request, 'admin': admin, 'books_request': books_request, 'page': page}
    )
