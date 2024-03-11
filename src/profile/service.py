from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_user, current_optional_user
from . import crud as profile_crud
import src.crud as base_crud
from src.database import RedisCache


async def view_user_information_in_profile(session: AsyncSession,
                                           user=Depends(current_optional_user)) -> dict | HTTPException:
    """
    1. This is really powerful function that returns all the books that ain't saved to profile
    but this books has it own ratings by user
    2. It returns user's profile image
    3. It returns all library columns by current user
    4. It uses hash by redis
    """
    if user:
        redis = RedisCache(f'user_and_books_not_in_profile.{user.id}')
        if await redis.check():
            data = await redis.get()
        else:
            # this is query to get user's profile pic
            profile_image = await profile_crud.read_users_profile_image(session, user)

            # here I'm getting all library columns by current user
            library = await profile_crud.read_all_library_columns_by_current_user(session, user)

            # finally getting books that user not saved to the profile but still has rating of it
            books_not_in_profile = await profile_crud.read_books_that_not_in_profile_with_rating(session, user)

            # executing data in memory with redis
            data = await redis.executor(
                data={'books_not_in_profile': books_not_in_profile, 'profile_pic': profile_image, 'library': library},
                ex=120)

        return data
    raise HTTPException(status_code=401)


async def view_books(session: AsyncSession, book_name: str, page: int = 1,
                     user=Depends(current_user)) -> dict:
    """
    Here is the function that will view all books that user has ever saved
    view_books() finding all user's books from database by its ID and is_saved_to_profile
    """
    if book_name:
        redis = RedisCache(f'books_pagination_in_profile.{user.id}?page={page}&name={book_name}')
    else:
        redis = RedisCache(f'books_in_profile.{user.id}?page={page}')

    if page > 0:
        # offset here means "skip first {offset} rows and show all rows next to it"
        # limit will always keep showing only 3 books in page
        offset = (page - 1) * 3
    else:
        raise HTTPException(status_code=403, detail={'Error': 'Forbidden'})

    if await redis.check():
        books = await redis.get()
    else:
        book_pagination = await profile_crud.read_books_in_profile(session=session, offset=offset,
                                                                   book_name=book_name, user=user)
        books = await redis.executor(
            data=book_pagination,
            ex=120)

    return {'books': books, 'page': page}


async def delete_book(book_id: int, session: AsyncSession, user=Depends(current_user)) -> None:
    if await base_crud.read_is_rating_exists(session, user, book_id):
        if await base_crud.read_is_book_saved_to_profile(session, user, book_id) is True:
            # now I should find book rating by user_id, using user_id and book_id is stmt
            await profile_crud.update_saved_profile(session=session, book_id=book_id,
                                                    user=user, is_saved_to_profile=False)
            # if user deleting book and set to it any rating - it changes is_saved_to_profile to False
        else:
            await profile_crud.delete_book_from_library(session,
                                                        user_id=str(user.id),
                                                        book_id=book_id,
                                                        is_saved_to_profile=False)
            # if user deleted book and do not set to it any rating - it delete book from library by owner
    else:
        # if user deleting book and didn't set any rating to it -
        # it deleting whole book from library by current user
        await profile_crud.delete_book_from_library(session,
                                                    user_id=str(user.id),
                                                    book_id=book_id,
                                                    is_saved_to_profile=False)
    await base_crud.delete_redis_cache_statement(f'user_and_books_not_in_profile',
                                                 'books_in_profile',
                                                 'best_books_rating')
