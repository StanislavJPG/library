from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.library.models import Book, Library
from src.library.service import get_url
from src.library.shemas import BookCreate


async def read_book_id(title: str, num: int, session: AsyncSession) -> Book | None:
    url = await get_url(title, num)
    book_id = await session.execute(select(Book.id).where(Book.url == url))
    return book_id.scalar_one_or_none()


async def create_book_and_change_data_for_library(title: str, num: int,
                                                  data: dict, info_book: dict, session: AsyncSession) -> dict:
    url = await get_url(title, num)
    url_orig = info_book['urls'][abs(num) % len(info_book['urls'])]

    await session.execute(
        insert(Book)
        .values(
            title=f'№{num}. «{info_book["title"]}»',
            image=info_book['image'],
            description=info_book['description'],
            url_orig=url_orig,
            url=url
        )
    )
    await session.commit()

    data['book_id'] = await session.scalar(select(Book.id).where(Book.url == url))
    return data


async def create_book_in_library(session: AsyncSession, **data) -> None:
    await session.execute(
        insert(Library)
        .values(**data)
    )
    await session.commit()


async def update_book_back_to_profile(session: AsyncSession, user: User, book_id: Book) -> None:
    await session.execute(
        update(Library)
        .values(is_saved_to_profile=True)
        .where(
            (Library.user_id == str(user.id)) &
            (Library.book_id == book_id))
    )
    await session.commit()


async def read_book_id_from_library_by_curr_user(session: AsyncSession, book: dict, user: User) -> Library:
    stmt = await session.scalar(
        select(Library.book_id)
        .where(
            (Library.book_id == book['book_id']) &
            (Library.user_id == str(user.id))
        )
    )
    return stmt


async def update_rating_by_book_and_curr_user(session: AsyncSession, book: dict, rating: int, user: User) -> None:
    await session.execute(
        update(Library)
        .values(rating=rating)
        .where(
            (Library.book_id == book['book_id']) &
            (Library.user_id == str(user.id)))
    )
    await session.commit()


async def read_book_url_orig_by_url(session: AsyncSession, book: str, num: int) -> Book:
    url = await get_url(book, num)
    stmt = await session.scalar(
        select(Book.url_orig)
        .where(
            Book.url == url
        )
    )
    return stmt


async def read_book_id_by_url(session: AsyncSession, book: str, num: int, url_orig: str) -> Book:
    url = await get_url(book, num)
    stmt = await session.scalar(
        select(Book.id)
        .where(
            (Book.url_orig == url_orig) &
            (Book.url == url)
        )
    )
    return stmt


async def read_is_book_in_database_by_title(session: AsyncSession, book: str | BookCreate) -> Book:
    is_has_query_already = await session.scalar(
        select(Book)
        .where(
            Book.title == f'№1. «{book.title}»'
        )
    )
    return is_has_query_already


async def create_book_by_users_request(session: AsyncSession, book: str | BookCreate) -> None:
    await session.execute(
        insert(Book)
        .values(
            title=f'«{book.title}»',
            image=book.image,
            description=book.description
        )
    )
    await session.commit()
