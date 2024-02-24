from sqlalchemy import select

from src.database import async_session_maker, RedisCash
from src.library.models import Library, Book


async def get_best_books():
    async with async_session_maker() as session:
        # Redis instance with value name
        redis = RedisCash('best_books_rating')
        is_cache_exists = await redis.check()

        if is_cache_exists:
            data = await redis.get()
        else:
            query_lib_books_with_rating = await session.scalars(select(Library.book_id).where(
                Library.rating.is_not(None)
            ))
            books_with_rating = query_lib_books_with_rating.all()
            # the task is quite simple: find a book that has owner(owners) and has rating

            query_books_have_no_owner = await session.scalars(select(Book.id).where(
                Book.id.notin_(books_with_rating)
            ))
            books_have_no_owner = query_books_have_no_owner.all()
            # can book have no owner? of course!
            # here I search for the book that have no owner(owners)

            query_find_books = await session.scalars(select(Book).where(
                (Book.id.in_(books_with_rating) & (Book.id.notin_(books_have_no_owner)))).limit(10))
            books = [entry.as_dict() for entry in query_find_books.all()]
            # finally: get all books that has any ratings and any owners

            query_users_ratings_counter = await session.scalars(select(Library).where(
                Library.rating.is_not(None)
            ))
            library = [{k: v for k, v in entry.as_dict().items() if k != 'user_id'}
                       for entry in query_users_ratings_counter.all()]

            # executing data with redis
            data = await redis.executor(data={'books': books, 'library': library}, ex=40)

    return data
