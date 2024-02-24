from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy import select
from fastapi.responses import HTMLResponse

from src.auth.base_config import current_optional_user
from src.base.router import templates
from src.database import async_session_maker
from src.library.models import Library, Book
from src.library.service import BookConnection, get_full_info
from src.library.shemas import RatingService

router = APIRouter(
    tags=['library_page']
)


@router.get('/library', response_class=HTMLResponse)
async def get_library_page(request: Request,
                           user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'user': user}
    )


@router.get('/library/{literature}', response_class=HTMLResponse)
async def library_search(request: Request, literature: str,
                         user=Depends(current_optional_user)):
    try:
        search_result = await get_full_info(literature)
    except ValueError:
        error_desc = 'Скоріш за все, ми не знайшли цю книгу :('

        return templates.TemplateResponse(
            'error.html',
            {'request': request, 'error': error_desc, 'user': user}, status_code=404)

    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'book': search_result, 'user_title': literature,
         'user': user})


@router.post('/library/save_book/{literature}')
async def save_book_page(literature: str,
                         num: int = Query(..., description='Number', gt=0),
                         user=Depends(current_optional_user)) -> None:
    # creating the instance of BookConnection class
    _database_conn = BookConnection(book=literature, num=num, user=user)
    # and use save_book_db method to save book to database
    await _database_conn.save_book_db()


@router.get('/read/{literature}', response_class=HTMLResponse)
async def get_read_page(request: Request, literature: str,
                        num: int = Query(..., description='Number', gt=0),
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

    return templates.TemplateResponse(
        'reader.html',
        {'request': request,
         'book': book, 'title': literature.title(), 'num': num, 'user': user, 'rating': rating}
    )


@router.post('/save_rating_to_database', response_model=None)
async def create_book_rating_by_user(rating_schema: RatingService, user=Depends(current_optional_user)) -> None:
    # creating the instance of BookConnection class
    _database_conn = BookConnection(rating_schema=rating_schema, user=user)
    # then save rating to database
    await _database_conn.save_rating_db()
