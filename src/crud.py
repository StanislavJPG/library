from sqlalchemy import select, insert, update, delete, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from src.auth.base_config import fastapi_users
from src.auth.models import User
from src.database import RedisCash
from src.library.models import Book, Library
from src.library.shemas import BookCreate


async def read_book_directly_from_db(session: AsyncSession, book: str) -> Book:
    stmt = await session.scalar(select(Book.url_orig).where(Book.title.like(f'%{book.split(" ")[0][1:]}%')))
    return stmt


async def update_users_pic(session: AsyncSession, user: fastapi_users, token: str) -> None:
    stmt = update(User).values(profile_image=token).where(
        User.id == str(user.id)
    )
    await session.execute(stmt)
    await session.commit()


async def get_url(title: str, num: int) -> str:
    url = f'http://127.0.0.1:8000/read/{title.lower()}?num={num}'
    return url


async def read_is_book_exists(title: str, num: int, session: AsyncSession) -> Book | None:
    url = await get_url(title, num)
    book_id = await session.scalar(select(Book.id).where(Book.url == url))

    return book_id


async def create_book_and_change_data_for_library(title: str, num: int,
                                                  data: dict, info_book, session: AsyncSession) -> dict:
    url = await get_url(title, num)
    url_orig = info_book['urls'][abs(num) % len(info_book['urls'])]

    await session.execute(insert(Book).values(
        title=f'№{num}. «{info_book["title"]}»',
        image=info_book['image'],
        description=info_book['description'],
        url_orig=url_orig,
        url=url
    ))
    await session.commit()

    data['book_id'] = await session.scalar(select(Book.id).where(Book.url == url))
    return data


async def create_book_in_library(session: AsyncSession, **data) -> None:
    await session.execute(insert(Library).values(**data))
    await session.commit()


async def read_is_book_saved_to_profile(session: AsyncSession, user: fastapi_users, book_id: Book | int
                                        ) -> Library | None:
    is_book_saved_to_profile = await session.scalar(select(Library.is_saved_to_profile).where(
        (Library.user_id == str(user.id)) & (Library.book_id == book_id)
    ))
    return is_book_saved_to_profile


async def update_book_back_to_profile(session: AsyncSession, user: fastapi_users, book_id: Book) -> None:
    await session.execute(update(Library).where((Library.user_id == str(user.id)) & (Library.book_id == book_id)))
    await session.commit()


async def read_book_id_from_library_by_curr_user(session: AsyncSession, book: dict, user: fastapi_users) -> Library:
    stmt = await session.scalar(select(Library.book_id).where(
        (Library.book_id == book['book_id']) & (Library.user_id == str(user.id))
    ))
    return stmt


async def update_rating_by_book_and_curr_user(session: AsyncSession, book: dict, rating: int, user: fastapi_users
                                              ) -> None:
    await session.execute(update(Library).where((Library.book_id == book['book_id']) &
                                                (Library.user_id == str(user.id))).values(rating=rating))
    await session.commit()


async def read_book_url_orig_by_url(session: AsyncSession, book: str, num: int) -> Book:
    url = await get_url(book, num)
    stmt = await session.scalar(select(Book.url_orig).where(
        Book.url == url
    ))
    return stmt


async def read_book_id_by_url(session: AsyncSession, book: str, num: int, url_orig: str) -> Book:
    url = await get_url(book, num)
    stmt = await session.scalar(select(Book.id).where(
        (Book.url_orig == url_orig) & (Book.url == url)
    ))
    return stmt


async def read_users_profile_image(session: AsyncSession, user: fastapi_users) -> User:
    stmt = await session.scalar(select(User.profile_image).where(User.id == str(user.id)))
    return stmt


async def read_all_library_columns_by_current_user(session: AsyncSession, user: fastapi_users) -> ScalarResult[Library]:
    stmt = await session.scalars(select(Library).where(Library.user_id == str(user.id)))
    return stmt


async def read_all_books_that_not_in_profile(session: AsyncSession, user: fastapi_users) -> ScalarResult[Library]:
    stmt = await session.scalars(select(Library.book_id).where((Library.user_id == str(user.id)) &
                                                               (Library.is_saved_to_profile.is_(False) &
                                                                (Library.rating.is_not(None)))))
    return stmt


async def read_books_that_not_in_profile_with_rating(session: AsyncSession, user: fastapi_users) -> list[dict]:
    books_ids = await read_all_books_that_not_in_profile(session, user)
    stmt = await session.scalars(select(Book).where(Book.id.in_(books_ids.all())).limit(5))
    return [x.as_dict() for x in stmt.all()]


async def read_is_rating_exists(session: AsyncSession, user: fastapi_users, book_id: int) -> Library:
    stmt = await session.scalar(select(Library.rating).where((Library.user_id == str(user.id))
                                                             & (Library.book_id == book_id)))
    return stmt


async def update_saved_profile(session: AsyncSession, book_id: int, is_saved_to_profile: bool, user: fastapi_users
                               ) -> None:
    await session.execute(update(Library).where(
        (Library.user_id == str(user.id)) & (Library.book_id == book_id)).values(
        is_saved_to_profile=is_saved_to_profile))
    await session.commit()


async def delete_book_from_library(session: AsyncSession, user: fastapi_users, book_id: int,
                                   set_is_saved_to_prof: bool = None) -> None:
    if set_is_saved_to_prof is None:
        await session.execute(delete(Library).where((Library.user_id == str(user.id)) & (Library.book_id == book_id)))
    else:
        await session.execute(delete(Library).where((Library.user_id == str(user.id)) & (Library.book_id == book_id) &
                                                    (Library.is_saved_to_profile.is_(set_is_saved_to_prof))))
    await session.commit()


async def read_specific_book_id_from_library(session: AsyncSession, user: fastapi_users) -> ScalarResult[Library]:
    stmt = await session.scalars(select(Library.book_id).where((Library.user_id == str(user.id)) &
                                 (Library.is_saved_to_profile.is_(True))))
    return stmt


async def read_books_in_profile_with_pagination(session: AsyncSession, offset: int, book_name: str,
                                                user: fastapi_users) -> list[dict]:
    specific_book_id = await read_specific_book_id_from_library(session=session, user=user)

    if book_name is None:
        # if book_name is None(by default), it shows all the user's books
        query_get_book = await session.scalars(select(Book).where(
            (Book.id.in_(specific_book_id.all()))).offset(offset).limit(3))

        # offset here means "skip first {offset} rows and show all rows next to it"
        # limit will always keep showing only 3 books in page
    else:
        # in any others cases it shows books, that user is looking for
        query_get_book = await session.scalars(select(Book).where(
            (Book.id.in_(specific_book_id.all()) & (Book.title.like(f'%{book_name[1:]}%')))
        ).offset(offset).limit(3))

    return [x.as_dict() for x in query_get_book.all()]


async def update_book_back_to_the_profile(session: AsyncSession, book_id: int, user: fastapi_users) -> None:
    await session.execute(update(Library).values(is_saved_to_profile=True).where(
        (Library.book_id == book_id) & (Library.user_id == str(user.id))
    ))
    await session.commit()
    await delete_redis_cache_statement()


async def read_is_book_in_database_by_title(session: AsyncSession, book: str | BookCreate) -> Book:
    is_has_query_already = await session.scalar(select(Book).where(
        Book.title == f'№1. «{book.title}»'
    ))
    return is_has_query_already


async def create_book_by_users_request(session: AsyncSession, book: str | BookCreate) -> None:
    await session.execute(insert(Book).values(
        title=f'«{book.title}»',
        image=book.image,
        description=book.description
    ))
    await session.commit()


async def delete_redis_cache_statement() -> None:
    redis = RedisCash()
    for instance in await redis.get_alike(f'books_in_profile', f'user_and_books_not_in_profile'):
        await redis.delete(instance)


async def read_is_book_exists_by_request(session: AsyncSession, book: BookCreate, query: list[dict]) -> bool:
    is_book_exists = await session.scalar(select(Book).where(
        (Book.title.in_(query)) & (Book.id == int(book.id))
    )) is not None
    return is_book_exists


async def update_book_args_by_admin(session: AsyncSession, book: BookCreate = None) -> None:
    await session.execute(update(Book).values(
        title=book.title,
        description=book.description,
        url=book.url,
        url_orig=book.url_orig
    ))
    await session.commit()


async def read_requested_books_for_admin(session: AsyncSession, offset: int) -> Sequence[Book]:
    stmt = await session.scalars(select(Book).where(
        (Book.title.isnot(None)) & (Book.image.isnot(None)) &
        (Book.url_orig.is_(None))).offset(offset).limit(4))
    return stmt.all()


async def read_books_for_top_rating(session: AsyncSession) -> dict:
    books_in_library_with_rating = await session.scalars(select(Library.book_id).where(
        Library.rating.is_not(None)
    ))
    # getting all the books that has any rating (limit 10)
    get_all_books_with_any_rating = await session.scalars(select(Book).where(
        (Book.id.in_(books_in_library_with_rating.all()))).limit(10))

    # serializing data to list[dict] for comfortable view
    books: list[dict] = [entry.as_dict() for entry in get_all_books_with_any_rating.all()]

    users_ratings_counter = await session.scalars(select(Library).where(
        Library.rating.is_not(None)
    ))
    # serializing data to list[dict] for comfortable view
    library: list[dict] = [{k: v for k, v in entry.as_dict().items() if k != 'user_id'}
                           for entry in users_ratings_counter.all()]

    return {'books': books, 'library': library}
