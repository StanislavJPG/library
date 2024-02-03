from fastapi import APIRouter, Depends
from sqlalchemy import select, update, delete, and_
from src.auth.base_config import current_optional_user, current_user
from src.auth.models import User
from src.database import async_session_maker
from src.library.models import Book, Library

test_profile = APIRouter(
    tags=['Profile_test']
)


# async def view_all_users_books(user=Depends(current_user)):
#     async with async_session_maker() as session:
#         select_book = select(Library.book_id).where(
#             (Library.user_id == str(user.id)) & (Library.is_saved_to_profile.is_(True))
#         )
#         current_user_book = await session.scalars(select_book)
#         all_books_info_from_db = current_user_book.all()
#
#         if all_books_info_from_db is not None:
#             stmt = await session.scalars(select(Book).where(
#                 Book.id.in_(all_books_info_from_db))
#             )
#         return stmt.all()


async def view_profile(user=Depends(current_user)):
    async with async_session_maker() as session:
        profile_image_query = select(User.profile_image
                                     ).where(User.id == str(user.id))
        profile_image = await session.scalars(profile_image_query)
        profile_image = profile_image.first()   # this is simple query to get user's profile pic

        query_users_ratings = await session.scalars(select(Library).where(
            Library.user_id == str(user.id)
        ))
        library = query_users_ratings.all()    # here I'm getting all library columns by current user

        query_books_ids = await session.scalars(select(Library.book_id).where(
            (Library.user_id == str(user.id)) & (Library.is_saved_to_profile.is_(False) &
                                                 (Library.rating.is_not(None)))
        ))   # here I'm asking for all books that are NOT saved to the profile
        books_ids = query_books_ids.all()

        query_books_not_in_profile = await session.scalars(select(Book).where(
            Book.id.in_(books_ids)
        ))   # finally getting books that user not saved to the profile but still has rating of it
        books_not_in_profile = query_books_not_in_profile.all()
    return books_not_in_profile, profile_image, library


async def delete_book(book_id: int, user=Depends(current_user)):
    async with async_session_maker() as session:
        is_rating_exists = await session.scalar(select(Library.rating).where(
            (Library.user_id == str(user.id)) & (Library.book_id == book_id)
        ))

        if is_rating_exists:
            is_book_saved_to_profile = await session.scalar(select(Library.is_saved_to_profile).where(
                (Library.user_id == str(user.id)) & (Library.book_id == book_id)
            ))

            if is_book_saved_to_profile is True:
                # now I should find book rating by user_id, using user_id and book_id is stmt
                stmt = update(Library).where(
                    (Library.user_id == str(user.id)) & (Library.book_id == book_id)
                ).values(
                    is_saved_to_profile=False
                )
                # if user deleting book and set to it any rating - it changes is_saved_to_profile to False
            else:
                stmt = delete(Library).where(
                    (Library.user_id == str(user.id)) & (Library.book_id == book_id) &
                    (Library.is_saved_to_profile.is_(False))
                )
                # if user deleted book and do not set to it any rating - it delete book from library by owner
        else:
            # if user deleting book and didn't set any rating to it -
            # it deleting whole book from library by current user
            stmt = delete(Library).where(
                (Library.user_id == str(user.id)) & (Library.book_id == book_id)
            )
        await session.execute(stmt)
        await session.commit()


async def view_books(book_name: str = None, user=Depends(current_user)):
    async with async_session_maker() as session:
        query_get_specific_book_id = await session.scalars(select(Library.book_id).where(
            (Library.user_id == str(user.id)) & (Library.is_saved_to_profile.is_(True))
        ))
        specific_book_id = query_get_specific_book_id.all()

        if book_name is None:
            # if book_name is None(by default), is shows all the user's books
            query_get_book = await session.scalars(select(Book).where(
                (Book.id.in_(specific_book_id))))
        else:
            # in any others cases it shows books, that user is looking for

            query_get_book = await session.scalars(select(Book).where(
                (Book.id.in_(specific_book_id) & (Book.title.like(f'%{book_name}%'))
                 )))
        book = query_get_book.all()
        return book

