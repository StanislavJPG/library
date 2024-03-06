from typing import Union

from fastapi import Depends, APIRouter, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import read_is_book_exists, read_is_rating_exists, read_is_book_in_database_by_title, \
    create_book_by_users_request
from src.library.service import BookSearchService, url_reader_by_user, save_book_database, save_rating_db
from src.library.shemas import RatingService, BookCreate
from src.auth.base_config import current_optional_user
from src.database import get_async_session


router = APIRouter(
    prefix='/api/library',
    tags=['library']
)


@router.get('/{literature}')
async def library_search_api(literature: str, session: AsyncSession = Depends(get_async_session),
                             user=Depends(current_optional_user)):
    try:    # getting book by user's request
        query_book_search = BookSearchService(literature, session)
        search_result = await query_book_search.get_full_info()
    except ValueError:
        error_desc = 'Скоріш за все, ми не знайшли цю книгу :('
        return {'error': error_desc, 'user': user}

    return {'book': search_result, 'user': user, 'error': ''}


@router.get('/read/{literature}')
async def get_read_page_api(literature: str, num: int = Query(..., description='Number', gt=0),
                            user=Depends(current_optional_user), session: AsyncSession = Depends(get_async_session)):
    book = await url_reader_by_user(session=session, book=literature, num=num)
    # use it to return full info about book

    # here I should find book's rating
    book_id = await read_is_book_exists(title=literature, num=num, session=session)
    if user:
        rating = await read_is_rating_exists(session=session, user=user, book_id=book_id)
    else:
        rating = None

    return {'book': book, 'rating': rating}


@router.post('/books/let_find', response_model=None)
async def create_temp_book_api(book: BookCreate, session: AsyncSession = Depends(get_async_session)) -> Union[None]:
    # user can make query to find book only if that book NOT in database already
    if await read_is_book_in_database_by_title(session=session, book=book) is None:
        await create_book_by_users_request(session=session, book=book)
    else:
        raise HTTPException(status_code=409)


@router.post('/save_book/{literature}', response_model=None)
async def save_book_page_api(literature: str,
                             num: int = Query(..., description='Number', gt=0),
                             user=Depends(current_optional_user), session=Depends(get_async_session)) -> None:
    # use save_book_db method to save book to database
    await save_book_database(book=literature, num=num, user=user, session=session)


@router.post('/save_rating_to_database', response_model=None)
async def create_book_rating_by_user_api(rating_schema: RatingService, user=Depends(current_optional_user),
                                         session=Depends(get_async_session)) -> None:
    # save rating to database
    await save_rating_db(rating_schema=rating_schema, user=user, session=session)
