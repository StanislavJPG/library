from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_user, current_optional_user
from src.crud import read_users_profile_image, read_all_library_columns_by_current_user, \
    read_books_that_not_in_profile_with_rating, read_is_rating_exists, read_is_book_saved_to_profile, update_saved_profile, \
    delete_book_from_library, read_books_in_profile_with_pagination, delete_redis_cache_statement
from src.database import RedisCash


async def view_profile_information(session: AsyncSession, user=Depends(current_optional_user)) -> dict | HTTPException:
    """
    1. This is really powerful function that returns all the books that ain't saved to profile
    but this books has it own ratings by user
    2. It returns user's profile image
    3. It returns all library columns by current user
    4. It uses hash by redis
    """
    if user:
        redis = RedisCash(f'user_and_books_not_in_profile.{user.id}')
        if await redis.check():
            data = await redis.get()
        else:
            # this is query to get user's profile pic
            profile_image = await read_users_profile_image(session, user)

            # here I'm getting all library columns by current user
            users_ratings = await read_all_library_columns_by_current_user(session, user)

            library = [{k: v for k, v in entry.as_dict().items() if k != 'user_id'}
                       for entry in users_ratings.all()]

            # finally getting books that user not saved to the profile but still has rating of it
            books_not_in_profile = await read_books_that_not_in_profile_with_rating(session, user)

            # executing data in memory with redis
            data = await redis.executor(
                data={'books': books_not_in_profile, 'image': profile_image, 'library': library},
                ex=20)

        return data
    raise HTTPException(status_code=401)


async def delete_book(book_id: int, session: AsyncSession, user=Depends(current_user)) -> None:
    if await read_is_rating_exists(session, user, book_id):
        if await read_is_book_saved_to_profile(session, user, book_id) is True:
            # now I should find book rating by user_id, using user_id and book_id is stmt
            await update_saved_profile(session=session, book_id=book_id, user=user, is_saved_to_profile=False)
            # if user deleting book and set to it any rating - it changes is_saved_to_profile to False
        else:
            await delete_book_from_library(session, user, book_id, set_is_saved_to_prof=False)
            # if user deleted book and do not set to it any rating - it delete book from library by owner
    else:
        # if user deleting book and didn't set any rating to it -
        # it deleting whole book from library by current user
        await delete_book_from_library(session, user, book_id)
    await delete_redis_cache_statement()


async def view_books(session: AsyncSession, book_name: str, page: int = 1,
                     user=Depends(current_user)) -> dict:
    """
    Here is the function that will view all books that user has ever saved
    view_books() finding all user's books from database by its ID and is_saved_to_profile
    """
    redis = RedisCash(f'books_in_profile.{user.id}&page={page}')
    if page > 0:
        # offset here means "skip first {offset} rows and show all rows next to it"
        # limit will always keep showing only 3 books in page
        offset = (page - 1) * 3
    else:
        raise HTTPException(status_code=403, detail={'Error': 'Forbidden'})

    if await redis.check():
        books = await redis.get()
    else:
        book_pagination = await read_books_in_profile_with_pagination(session, offset, book_name, user)
        books = await redis.executor(
            data=book_pagination,
            ex=20)

    return {'books': books, 'page': page}
