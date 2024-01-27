from functools import reduce
from urllib.parse import quote, unquote

from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy import select, update, insert
from sqlalchemy.sql.functions import coalesce

from src.auth.base_config import current_optional_user, current_user
from src.base.router import templates
from src.database import async_session_maker
from src.library.models import Book, BookRating
from src.library.service import get_full_info, save_book_to_database, get_book_attr_by_user
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
        url_by_user = await get_book_attr_by_user(user.id, Book.url)

        async with async_session_maker() as session:
            if url_from_current_cite in url_by_user:
                check_if_rating = select(Book.user_rating).where((Book.owner_id == str(user.id))
                                                                 & (Book.url == url_from_current_cite))
                scalars_request = await session.scalars(check_if_rating)
                is_rating = scalars_request.all()

                stmt = select(Book.url_orig).where(Book.url == url_from_current_cite)
                book_session = await session.scalars(stmt)
                book = book_session.first()    # this is necessary for quick load url directly from db (if it exists)

            else:
                # stmt = select(BookRating.url_orig).where(
                #     BookRating.url_orig == 'pass')

                book = await book_url_getter_to_read(literature, num)
                is_rating = None
    else:
        book = await book_url_getter_to_read(literature, num)

    return templates.TemplateResponse(
        'reader.html',
        {'request': request,
         'book': book, 'title': literature.title(), 'num': num, 'user': user, 'rating': is_rating}
    )


@router.post('/save_rating_to_database')
async def book_rating_maker_by_user(rating_schema: RatingService, user=Depends(current_user)):
    async with async_session_maker() as session:
        stmt = update(Book).values(user_rating=rating_schema.user_rating).where(
            (Book.owner_id == str(user.id)) & (Book.url_orig == rating_schema.current_book_url))

        await session.execute(stmt)
        await session.commit()

        stmt_users = select(Book.user_rating).where(Book.url_orig == rating_schema.current_book_url)
        users_scalars = await session.scalars(stmt_users)
        all_users_rating = users_scalars.all()

        summary = 0
        for rating in all_users_rating:
            summary += rating
        general_rating_statistic = summary / (len([x for x in all_users_rating if x is not None]))
        # print(general_rating_statistic)

        stmt_check = select(BookRating).where(BookRating.url_orig == rating_schema.current_book_url)
        column_exists = await session.execute(stmt_check)
        column_exists = column_exists.first() is not None

        if not column_exists:
            inserting_rating_stmt = insert(BookRating).values(url_orig=rating_schema.current_book_url,
                                                              general_rating=general_rating_statistic)
            await session.execute(inserting_rating_stmt)
            await session.commit()
        else:
            rating_new_stmt = update(BookRating).values(general_rating=general_rating_statistic).where(
                BookRating.url_orig == rating_schema.current_book_url
            )
            await session.execute(rating_new_stmt)
            await session.commit()

        # logic is implement new models, that will accumulate all rating
        # by specific book.

        # Or you can definitely make something with summary / (len([x for x in all_users if x is not None]))
        # hmm???
