from fastapi import Depends, HTTPException
from sqlalchemy import select, update, delete

from src.auth.base_config import current_user
from src.auth.models import User
from src.database import async_session_maker, RedisCash
from src.library.models import Book, Library


async def view_profile_information(user=Depends(current_user)) -> dict:
    """
    1. This is really powerful function that returns all the books that ain't saved to profile
    but this books has it own ratings by user
    2. It returns user's profile image
    3. It returns all library columns by current user
    4. It uses hash by redis
    """
    async with async_session_maker() as session:
        redis = RedisCash(f'user_profile.{user.id}')
        is_cache_exists = await redis.check()

        if is_cache_exists:
            data = await redis.get()
        else:
            # this is simple query to get user's profile pic
            profile_image_query = select(User.profile_image).where(User.id == str(user.id))
            profile_image = await session.scalars(profile_image_query)
            profile_image = profile_image.first()

            # here I'm getting all library columns by current user
            query_users_ratings = await session.scalars(select(Library).where(
                Library.user_id == str(user.id)
            ))

            library = [{k: v for k, v in entry.as_dict().items() if k != 'user_id'}
                       for entry in query_users_ratings.all()]

            # here I'm asking for all books that are NOT saved to the profile
            query_books_ids = await session.scalars(select(Library.book_id).where(
                (Library.user_id == str(user.id)) & (Library.is_saved_to_profile.is_(False) &
                                                     (Library.rating.is_not(None)))
            ))
            books_ids = query_books_ids.all()

            # finally getting books that user not saved to the profile but still has rating of it
            query_books_not_in_profile = await session.scalars(select(Book).where(
                Book.id.in_(books_ids)
            ).limit(5))
            books_not_in_profile = [x.as_dict() for x in query_books_not_in_profile.all()]

            # executing data in memory with redis
            data = await redis.executor(
                data={'books': books_not_in_profile, 'image': profile_image, 'library': library},
                ex=20)

    return data


async def delete_book(book_id: int, user=Depends(current_user)) -> None:
    async with async_session_maker() as session:
        redis = RedisCash(f'user_profile.{user.id}')

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
                # after that - deleting cache from redis
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

        await redis.delete()
        await session.execute(stmt)
        await session.commit()


async def view_books(book_name: str, page: int = 1, user: User = current_user, per_page: int = 3) -> dict:
    async with async_session_maker() as session:
        """
        Here I am implementing function that will view all books that user has ever saved
        view_books() finding all user's books from database by its ID and is_saved_to_profile
        """
        query_get_specific_book_id = await session.scalars(select(Library.book_id).where(
            (Library.user_id == str(user.id)) & (Library.is_saved_to_profile.is_(True))
        ))
        specific_book_id = query_get_specific_book_id.all()

        if page > 0:
            offset = (page - 1) * 3
        else:
            raise HTTPException(status_code=403, detail={'Error': 'Forbidden'})

        if book_name is None:
            # if book_name is None(by default), it shows all the user's books
            query_get_book = await session.scalars(select(Book).where(
                (Book.id.in_(specific_book_id))).offset(offset).limit(per_page))

            # offset here means "skip first {offset} rows and show all rows next to it"
            # limit will always keep showing only 3 books in page

        else:
            # in any others cases it shows books, that user is looking for
            query_get_book = await session.scalars(select(Book).where(
                (Book.id.in_(specific_book_id) & (Book.title.like(f'%{book_name[1:]}%')))
            ).offset(offset).limit(per_page))

        books = query_get_book.all()

        return {'books': books, 'page': page}
