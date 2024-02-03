from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy import select, update, insert

from src.auth.base_config import current_optional_user
from src.base.router import templates
from src.database import async_session_maker
from src.library.models import Book, Library
from src.library.service import get_full_info, save_book_db, reader_session_by_user, book_url_getter_to_read
from src.library.shemas import RatingService

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
                         num: int = Query(..., description='Number', gt=0),
                         user=Depends(current_optional_user)):
    database = await save_book_db(literature, num, user)

    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'user_title': literature,
         'database': database, 'user': user}
    )


@router.get('/read/{literature}')
async def get_read_page(request: Request, literature: str,
                        num: int = Query(..., description='Number', gt=0),
                        user=Depends(current_optional_user)):

    # url_from_current_cite = f'http://127.0.0.1:8000/read/{literature.lower()}?num={num}'
    # async with async_session_maker() as session:
    if user:
        book = await reader_session_by_user(literature, num)

    else:
        book = await reader_session_by_user(literature, num)

    return templates.TemplateResponse(
        'reader.html',
        {'request': request,
         'book': book, 'title': literature.title(), 'num': num, 'user': user}
    )


@router.post('/save_rating_to_database')
async def book_rating_maker_by_user(rating_schema: RatingService, user=Depends(current_optional_user)):
    async with async_session_maker() as session:
        query_get_id = await session.scalars(select(Book.id).where(
            Book.url_orig == rating_schema.current_book_url
        ))
        book_id = query_get_id.first()

        query_has_book = await session.scalars(select(Library.book_id).where(
            (Library.book_id == int(book_id)) & (Library.user_id == str(user.id))
        ))
        has_book = query_has_book.first()

        if has_book is not None:
            stmt = update(Library).values(rating=rating_schema.user_rating).where(
                (Library.book_id == int(book_id)) & (Library.user_id == str(user.id))
            )
        else:
            if book_id is None:
                url = f'http://127.0.0.1:8000/read/{rating_schema.title.lower()}?num={rating_schema.num}'
                info_book_func = await book_url_getter_to_read(rating_schema.title.lower(), rating_schema.num)
                info_book = info_book_func[0]
                url_orig = info_book_func[-1]

                stmt_save = insert(Book).values(
                    title=f'№{rating_schema.num}. {info_book[1]}',
                    image=info_book[0],
                    description=info_book[2],
                    url_orig=url_orig,
                    url=url,
                )
                await session.execute(stmt_save)

            stmt = insert(Library).values(
                user_id=user.id,
                book_id=book_id,
                rating=rating_schema.user_rating,
                is_saved_to_profile=False
            )

        await session.execute(stmt)
        await session.commit()
