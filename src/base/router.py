from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Depends
from sqlalchemy import select, desc

from src.auth.base_config import current_optional_user
from src.database import async_session_maker
from src.library.models import Book, BookRating

router = APIRouter(
    tags=['Base_page']
)

templates = Jinja2Templates(directory='src/templates')


@router.get('/')
async def get_base_page(request: Request, user=Depends(current_optional_user)):
    async with async_session_maker() as session:
        stmt2 = select(BookRating)
        stmt2_scalars = await session.scalars(stmt2)
        ratings = stmt2_scalars.all()

        stmt = select(Book).limit(limit=10).where(Book.user_rating != 0).order_by(desc(Book.user_rating))

        stmt_scalars = await session.scalars(stmt)
        books = stmt_scalars.all()

        exclude = ['id', 'owner_id', 'user_rating']
        unique_books = set()

        filtered_books = [
            {key: value for key, value in book.as_dict().items() if key not in exclude}
            for book in books
            if (filtered := tuple((key, value) for key, value in book.as_dict().items() if
                                  key not in exclude)) not in unique_books and not unique_books.add(filtered)
        ]

        books = [book for book in filtered_books if book['url_orig']
                 in [rating.as_dict()['url_orig'] for rating in ratings]]
        # print(books)

    return templates.TemplateResponse(
        'base.html',
        {'request': request, 'user': user, 'books': books,
         'ratings': ratings}
    )


@router.get('/test/')
async def stest():
    async with async_session_maker() as session:
        stmt = select(Book).limit(limit=10).where(Book.user_rating != 0).order_by(desc(Book.user_rating))

        stmt_scalars = await session.scalars(stmt)
        books = stmt_scalars.all()
    return [x.as_dict()['url_orig'] for x in books]
