from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.library.models import Library, Book


async def read_all_library_columns_by_current_user(session: AsyncSession, user: User):
    query = (select(
        Library.book_id,
        Library.rating,
        Library.is_saved_to_profile)
        .filter_by(
            user_id=str(user.id)
        )
    )
    stmt = await session.execute(query)
    return [{"book_id": c[0],
             "rating": c[1],
             "is_saved_to_profile": c[2]} for c in stmt.all()]


async def read_books_that_not_in_profile_with_rating(session: AsyncSession, user: User) -> list[dict]:
    stmt = await session.execute(
        select(Book.id, Book.title, Book.image, Book.url)
        .where(Book.id.in_(
            select(Library.book_id)
            .where(
                (Library.user_id == str(user.id)) &
                (Library.is_saved_to_profile.is_(False)) &
                (Library.rating.is_not(None))
            )
        ))
        .limit(10)
    )
    return [{"id": c[0],
             "title": c[1],
             "image": c[2],
             "url": c[3]} for c in stmt.all()]


async def update_saved_profile(session: AsyncSession, book_id: int,
                               is_saved_to_profile: bool, user: User) -> None:
    await session.execute(
        update(Library)
        .where(
            (Library.user_id == str(user.id)) &
            (Library.book_id == book_id))
        .values(
            is_saved_to_profile=is_saved_to_profile)
    )
    await session.commit()


async def delete_book_from_library(session: AsyncSession, **kwargs) -> None:
    await session.execute(delete(Library).filter_by(**kwargs))
    await session.commit()


async def read_books_in_profile(session: AsyncSession, offset: int, book_name: str, user: User) -> list[dict]:
    specific_book_id = await session.scalars(
        select(Library.book_id)
        .filter_by(
            user_id=str(user.id),
            is_saved_to_profile=True)
    )

    if book_name is None:
        # if book_name is None(by default), it shows all the user's books
        query_get_book = await session.scalars(
            select(Book)
            .where(
                (Book.id.in_(specific_book_id.all())))
            .offset(offset)
            .limit(3)
        )
        # offset here means "skip first {offset} rows and show all rows next to it"
        # limit will always keep showing only 3 books in page
    else:
        # in any others cases it shows books, that user is looking for
        query_get_book = await session.scalars(
            select(Book)
            .where(
                (Book.id.in_(specific_book_id)) &
                (
                        (Book.title.like(f'%{book_name}%')) |
                        (Book.title.like(f'%{book_name.title()}%'))
                )
            )
            .offset(offset)
            .limit(3)
        )
    return [x.as_dict() for x in query_get_book.all()]
