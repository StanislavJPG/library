from sqlalchemy import select

from src.database import async_session_maker
from src.library.models import Library, Book


async def get_top_books():
    async with async_session_maker() as session:
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
        books = query_find_books.all()
        # finally: get all books that has any ratings and any owners

        query_users_ratings_counter = await session.scalars(select(Library).where(
            Library.rating.is_not(None)
        ))
        library = query_users_ratings_counter.all()
    return books, library
