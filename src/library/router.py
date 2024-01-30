from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy import select, update, insert
from sqlalchemy.sql.functions import coalesce

from src.auth.base_config import current_optional_user, current_user
from src.base.router import templates
from src.database import async_session_maker
from src.library.models import Book, BookRating
from src.library.service import get_full_info, save_book_to_database, get_book_attr_by_user, reader_session_by_user
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


@router.get('/read/{literature}')
async def get_read_page(request: Request, literature: str,
                        num: int = Query(..., description='Number', gt=0),
                        user=Depends(current_optional_user)):

    url_from_current_cite = f'http://127.0.0.1:8000/read/{literature.lower()}?num={num}'
    async with async_session_maker() as session:
        if user:
            url_by_user = await get_book_attr_by_user(user.id, Book.url)

            if url_from_current_cite in url_by_user:
                check_if_rating = select(Book.user_rating).where((Book.owner_id == str(user.id))
                                                                 & (Book.url == url_from_current_cite))
                scalars_request = await session.scalars(check_if_rating)
                is_rating = scalars_request.all()

                stmt = select(Book.url_orig).where(Book.url == url_from_current_cite)
                # stmt = select(BookRating.url_orig).where(BookRating.url == url_from_current_cite)
                book_session = await session.scalars(stmt)
                book = book_session.first()    # this is necessary for quick load url directly from db (if it exists)

            else:
                book = await reader_session_by_user(literature, num)
                is_rating = None
        else:
            book = await reader_session_by_user(literature, num)

            is_rating = None

    return templates.TemplateResponse(
        'reader.html',
        {'request': request,
         'book': book, 'title': literature.title(), 'num': num, 'user': user, 'rating': is_rating}
    )


@router.post('/save_rating_to_database')
async def book_rating_maker_by_user(rating_schema: RatingService, user=Depends(current_user)):
    async with async_session_maker() as session:
        stmt_is_rating_exists = select(Book.user_rating).where(
            (Book.owner_id == str(user.id)) & (Book.url_orig == rating_schema.current_book_url))
        is_rating = await session.scalars(stmt_is_rating_exists)
        is_rating_exists = is_rating.first()

        stmt_is_book_exists = select(Book).where(
            (Book.owner_id == str(user.id)) & (Book.url_orig == rating_schema.current_book_url))
        is_book_exists = await session.scalars(stmt_is_book_exists)
        is_book_exists = is_book_exists.first()

        # 1 case - when user have this book in db, but have no rating yet
        # 2 case - when user do NOT have this book in db, but have rating yet

        if is_book_exists is not None:
            stmt = update(Book).values(user_rating=rating_schema.user_rating).where(
                (Book.owner_id == str(user.id)) & (Book.url_orig == rating_schema.current_book_url))
        else:
            if is_rating_exists is None and is_book_exists is None:
                info = await get_full_info(rating_schema.title)
                stmt = insert(Book).values(
                    title=f'№{rating_schema.num}. {rating_schema.title}',
                    image=info[0],
                    description=info[2],
                    url_orig=rating_schema.current_book_url,
                    url=f'http://127.0.0.1:8000/read/{rating_schema.title.lower()}?num={rating_schema.num}',
                    owner_id=user.id,
                    user_rating=rating_schema.user_rating,
                    saved_to_profile=False
                )
            else:
                stmt = update(Book).values(user_rating=rating_schema.user_rating).where(
                    (Book.owner_id == str(user.id)) & (Book.url_orig == rating_schema.current_book_url))

        await session.execute(stmt)
        await session.commit()

        stmt_check_column = select(BookRating).where(BookRating.url_orig == rating_schema.current_book_url)
        column_exists = await session.execute(stmt_check_column)
        column_not_exists = column_exists.first() is None

        if column_not_exists:
            info = await get_full_info(rating_schema.title)
            inserting_rating_stmt = insert(BookRating).values(
                url_orig=rating_schema.current_book_url,
                url=f'http://127.0.0.1:8000/read/{rating_schema.title.lower()}?num={rating_schema.num}',
                title=f'{rating_schema.num}. {rating_schema.title}',
                image=info[0],
                description=info[2],
                rating=rating_schema.user_rating,
                rating_count=1
            )
            await session.execute(inserting_rating_stmt)
            await session.commit()
        else:
            if is_rating_exists is None:

                rating_new_stmt = update(BookRating).values(
                    rating=coalesce(BookRating.rating, 0) + rating_schema.user_rating,
                    rating_count=coalesce(BookRating.rating_count, 0) + 1).where(
                    BookRating.url_orig == rating_schema.current_book_url
                )
            else:
                rating_new_stmt = update(BookRating).values(
                    rating=(coalesce(BookRating.rating) - is_rating_exists) + rating_schema.user_rating
                ).where(BookRating.url_orig == rating_schema.current_book_url)

            await session.execute(rating_new_stmt)
            await session.commit()
