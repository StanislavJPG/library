from typing import Union

from fastapi import Depends, APIRouter, Query, HTTPException
from sqlalchemy import select, insert

from src.library.models import Book
from src.library.service import BookSearchService, BookConnection
from src.library.shemas import RatingService, BookCreate
from src.auth.base_config import current_optional_user
from src.database import async_session_maker
from src.library.models import Library


router = APIRouter(
    prefix='/api/library',
    tags=['library']
)


@router.get('/{literature}')
async def library_search_api(literature: str, user=Depends(current_optional_user)):
    try:    # getting book by user's request
        query_book_search = BookSearchService(literature)
        search_result = await query_book_search.get_full_info()
    except ValueError:
        error_desc = 'Скоріш за все, ми не знайшли цю книгу :('
        return {'error': error_desc, 'user': user}

    return {'book': search_result, 'user': user, 'error': ''}


@router.get('/read/{literature}')
async def get_read_page_api(literature: str, num: int = Query(..., description='Number', gt=0),
                            user=Depends(current_optional_user)):
    # creating the instance of BookConnection class
    _database_conn = BookConnection(book=literature, num=num, user=user)
    # and use it to return full info about book
    book = await _database_conn.url_reader_by_user()

    async with async_session_maker() as session:
        """
        here I should find book's rating
        """
        url_from_current_cite = f'http://127.0.0.1:8000/read/{literature.lower()}?num={num}'

        book_id = await session.scalar(select(Book.id).where(Book.url == url_from_current_cite))

        if user:
            rating = await session.scalar(select(Library.rating).where(
                (Library.user_id == str(user.id)) & (Library.book_id == book_id)
            ))
        else:
            rating = None

    return {'book': book, 'rating': rating}


@router.post('/books/let_find', response_model=None)
async def create_temp_book_api(book: BookCreate) -> Union[None]:
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


@router.post('/save_book/{literature}', response_model=None)
async def save_book_page_api(literature: str,
                             num: int = Query(..., description='Number', gt=0),
                             user=Depends(current_optional_user)) -> None:
    # creating the instance of BookConnection class
    _database_conn = BookConnection(book=literature, num=num, user=user)
    # and use save_book_db method to save book to database
    await _database_conn.save_book_db()


@router.post('/save_rating_to_database', response_model=None)
async def create_book_rating_by_user_api(rating_schema: RatingService, user=Depends(current_optional_user)) -> None:
    # creating the instance of BookConnection class
    _database_conn = BookConnection(rating_schema=rating_schema, user=user)
    # then save rating to database
    await _database_conn.save_rating_db()
