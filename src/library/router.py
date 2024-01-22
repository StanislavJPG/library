from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy import select

from src.auth.base_config import current_optional_user
from src.base.router import templates
from src.database import async_session_maker
from src.library.models import Book
from src.library.service import get_full_info, save_book_to_database, get_book_by_user

router = APIRouter(
    tags=['Library_page']
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
    search_result = await get_full_info(literature)

    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'book': search_result, 'user_title': literature,
         'user': user})


@router.post('/library/save_book/{literature}')
async def save_book_page(request: Request, literature: str,
                         num: int = Query(..., description='Number'),
                         user=Depends(current_optional_user)):
    database = await save_book_to_database(literature, num, user)

    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'user_title': literature,
         'database': database, 'user': user}
    )


async def book_url_getter_to_read(literature: str, num: int):
    info_book = await get_full_info(literature)
    book = info_book[4][abs(num) % len(info_book[4])]
    return book


@router.get('/read/{literature}')
async def get_read_page(request: Request, literature: str,
                        num: int = Query(..., description='Number', gt=0),
                        user=Depends(current_optional_user)):

    url_from_current_cite = f'http://127.0.0.1:8000/read/{literature.lower()}?num={num}'

    if user:
        from_database = await get_book_by_user(user.id)

        if url_from_current_cite in [x.as_dict()['url'] for x in from_database]:
            async with async_session_maker() as session:
                stmt = select(Book.url_orig).where(Book.url == url_from_current_cite)
                book_session = await session.scalars(stmt)
                book = book_session.first()    # this is necessary for quick load url directly from db (if it exists)
        else:
            book = await book_url_getter_to_read(literature, num)
    else:
        book = await book_url_getter_to_read(literature, num)

    return templates.TemplateResponse(
        'reader.html',
        {'request': request,
         'book': book, 'title': literature.title(), 'num': num, 'user': user}
    )
