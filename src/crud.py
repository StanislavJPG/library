from sqlalchemy import select, update, func, cast, Float, join, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import fastapi_users
from src.database import RedisCache
from src.auth.models import User
from src.library.models import Book, Library


async def read_book_directly_from_db(session: AsyncSession, book: str) -> Book:
    stmt = await session.scalar(
        select(Book.url_orig)
        .where(
            (Book.title.ilike(f'%{book.lower()}%')) |
            ((Book.title.ilike(f'%{book.title()}%')) &
             (Book.url.isnot(None)))
        )
    )
    return stmt


async def update_users_pic(session: AsyncSession, user: fastapi_users, token: str) -> None:
    stmt = update(User).values(profile_image=token).filter_by(id=str(user.id))
    await session.execute(stmt)
    await session.commit()


async def read_is_book_saved_to_profile(session: AsyncSession, user: User, book_id: Book | int
                                        ) -> Library | None:
    is_book_saved_to_profile = await session.scalar(
        select(Library.is_saved_to_profile)
        .where(
            (Library.user_id == str(user.id)) &
            (Library.book_id == book_id)
        )
    )
    return is_book_saved_to_profile


async def update_book_back_to_the_profile(session: AsyncSession, book_id: int, user: fastapi_users) -> None:
    await session.execute(
        update(Library)
        .values(is_saved_to_profile=True)
        .where(
            (Library.book_id == book_id) &
            (Library.user_id == str(user.id))
        )
    )
    await session.commit()
    await delete_redis_cache_statement(f'books_in_profile', f'books_not_in_profile')


async def read_is_rating_exists(session: AsyncSession, user: User, book_id: int) -> Library:
    stmt = await session.scalar(
        select(Library.rating)
        .where(
            (Library.user_id == str(user.id)) &
            (Library.book_id == book_id))
    )
    return stmt


async def delete_redis_cache_statement(*args) -> None:
    redis = RedisCache()
    for arg in args:
        for instance in await redis.get_alike(arg):
            await redis.delete(instance)


async def read_books_for_top_rating(session: AsyncSession) -> list[dict]:
    """
    :param session:
    :return: list[dict] with values that was counted from database
    (using type of list because of iteration needs for the frontend jinja)
    """
    ratings_avg = await session.execute(
        select(
            Book,
            cast(func.avg(Library.rating), Float).label('avg_rating'),
            cast(func.count(Library.rating), Integer).label('users_counter')
        )
        .select_from(
            join(Library, Book)
        )
        .where(Library.rating.is_not(None))
        .group_by(Book)
        .having(cast(func.avg(Library.rating), Float).label('avg_rating') >= 4)
        .limit(10)
        .order_by(cast(func.avg(Library.rating), Float).label('avg_rating').desc())
    )
    # serializing data to list[dict] for comfortable view
    top_books_statistic: list[dict] = [{**c[0].as_dict(), "average": c[1], "counter": c[2]} for c in ratings_avg.all()]
    return top_books_statistic
