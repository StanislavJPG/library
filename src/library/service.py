from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_optional_user
from . import crud as library_crud
import src.crud as base_crud
from src.database import RedisCache
from fastapi import status

from src.library.scraper import BookSearchService
from src.library.shemas import RatingService


async def save_book_database(book: str, num: int, session: AsyncSession,
                             rating: int = None, user=Depends(current_optional_user)) -> None:
    book_id = await library_crud.read_book_id(book, num, session)
    data = {
        'user_id': str(user.id),
        'book_id': book_id,
        'rating': rating,
        'is_saved_to_profile': True
    }
    # Creating book in tables (Book, Library) if book is not exists in database
    if book_id is None:
        info_book = await BookSearchService(book).get_full_book_info()
        data = await library_crud.create_book_and_change_data_for_library(book, num, data, info_book, session)
        await library_crud.create_book_in_library(session, **data)
    else:
        # in other case it checks is the book is saved to profile
        is_book_saved_to_profile = await base_crud.read_is_book_saved_to_profile(session, user, book_id)

        # creating book by user in Library if it's not
        if is_book_saved_to_profile is None:
            await library_crud.create_book_in_library(session, **data)
        # in other case it checks is the argument `is_saved_to_profile` is True of False
        # pulls book to profile if it's False
        else:
            if is_book_saved_to_profile is False:
                await library_crud.update_book_back_to_profile(session, user, book_id)
            # raising HTTPException if it's True (CONFLICT 409)
            else:
                raise HTTPException(status_code=409, detail=status.HTTP_409_CONFLICT)
    # clearing all the cache after all the operations with book
    # await redis.delete()
    await base_crud.delete_redis_cache_statement(f'books_not_in_profile', 'books_in_profile')


async def save_rating_db(rating_schema: RatingService,
                         session: AsyncSession,
                         user=Depends(current_optional_user)) -> None:
    # book_id returning book's id and url from table Book
    book = await get_book_id(session, rating_schema)
    # taking book id from table Library by current user (if it exists)
    book_id = await library_crud.read_book_id_from_library_by_curr_user(session=session, book=book, user=user)

    # updating if book_id exists
    if book_id is not None:
        # if book exists it updates rating to new value
        await library_crud.update_rating_by_book_and_curr_user(session, book, rating_schema.user_rating, user)
    else:
        if book['book_id'] is None:
            """
            If book does not exist in book table and in library table -
             - It's creating a new book in book table and library table + rating
            """
            await save_book_database(book=rating_schema.title, rating=rating_schema.user_rating,
                                     num=rating_schema.num, user=user, session=session)

        book = await get_book_id(session=session, rating_schema=rating_schema)

        data = {'user_id': user.id,
                'book_id': book['book_id'],
                'rating': rating_schema.user_rating,
                'is_saved_to_profile': False}
        # book will NOT be saved in profile if user set any rating but DOES NOT save a book
        await library_crud.create_book_in_library(session, **data)

    # when user making any operations with book in profile it updates hash by deleting it
    # (and then after updating a page it's making again)
    await base_crud.delete_redis_cache_statement(f'books_not_in_profile',
                                                 'books_in_profile',
                                                 'best_books_rating')


async def url_reader_by_user(session: AsyncSession, book, num) -> str:
    """
    This endpoint made for keep "DRY"
    It's created for getting book's ORIGINAL url directly from database if it exists
    But it will search books at first if it's not
    """
    redis = RedisCache(f'{book.lower()}.{num}')
    query_book_search = BookSearchService(book)

    query_book = await library_crud.read_book_url_orig_by_url(session=session, book=book, num=num)

    if query_book is None:
        book_func = await query_book_search.get_read_url(num)
        book_url = book_func['book']
    else:
        book_url = query_book

    book = await redis.executor(data=book_url, ex=120)

    return book


async def get_book_id(session: AsyncSession, rating_schema: RatingService) -> dict:
    """
    Taking specific book id from database
    """
    url = await get_url(rating_schema.title, rating_schema.num)
    book_id = await library_crud.read_book_id_by_url(session, rating_schema.title,
                                                     rating_schema.num, url_orig=rating_schema.current_book_url)
    return {'book_id': book_id, 'url': url}


async def get_url(title: str, num: int) -> str:
    url = f'http://127.0.0.1:8000/read/{title.lower()}?num={num}'
    return url
