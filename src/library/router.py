from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy import select

from src.auth.base_config import current_optional_user
from src.base.router import templates
from src.database import async_session_maker, RedisHash
from src.library.models import Library, Book
from src.library.service import reader_session_by_user, BookService, DatabaseInteract
from src.library.shemas import RatingService

router = APIRouter(
    tags=['library_page']
)


@router.get('/library')
async def get_library_page(request: Request,
                           user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'user': user}
    )


@router.get('/library/{literature}')
async def library_search(request: Request, literature: str,
                         user=Depends(current_optional_user)):
    try:
        search_result = await BookService.get_full_info(literature)
    except ValueError:
        return templates.TemplateResponse(
            'error.html',
            {'request': request, 'error': 'Скоріш за все, ми не знайшли цю книгу :(', 'user': user}, status_code=404)

    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'book': search_result, 'user_title': literature,
         'user': user})


@router.post('/library/save_book/{literature}')
async def save_book_page(request: Request, literature: str,
                         num: int = Query(..., description='Number', gt=0),
                         user=Depends(current_optional_user)):

    database = await DatabaseInteract.save_book_db(literature, num, user)

    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'user_title': literature,
         'database': database, 'user': user}
    )


@router.get('/read/{literature}')
async def get_read_page(request: Request, literature: str,
                        num: int = Query(..., description='Number', gt=0),
                        user=Depends(current_optional_user)):
    book = await reader_session_by_user(literature, num)

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


@router.post('/save_rating_to_database')
async def book_rating_maker_by_user(rating_schema: RatingService, user=Depends(current_optional_user)):
    await DatabaseInteract.save_rating_db(rating_schema, user)
