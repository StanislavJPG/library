from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import update

from src.auth.base_config import current_optional_user
from src.database import async_session_maker, RedisCash
from src.library.models import Library
from src.profile.service import view_profile_information, delete_book, view_books

router = APIRouter(
    prefix='/api',
    tags=['profile']
)


@router.get('/profile')
async def get_profile_api(book_name: Optional[str] = None,
                          page: Optional[int] = 1, user=Depends(current_optional_user),
                          profile_data=Depends(view_profile_information)):

    books_in_profile = await view_books(book_name, page, user)

    return {'books_in_profile': books_in_profile['books'],
            'page': books_in_profile['page'],
            'books_not_in_profile': profile_data['books'], 'profile_image': profile_data['image'],
            'library': profile_data['library']}


@router.delete('/books/{book_id}', response_model=None)
async def delete_book_from_profile_api(book_id: int, user=Depends(current_optional_user)) -> None:
    await delete_book(book_id, user)


@router.put('/save_back/{book_id}', response_model=None)
async def save_book_back_to_profile_api(book_id: int, user=Depends(current_optional_user)):
    """
    endpoint for change is_saved_to_profile to True (to save book to the profile)
    """
    async with async_session_maker() as session:
        redis = RedisCash(f'user_profile.{user.id}')

        stmt = update(Library).values(is_saved_to_profile=True).where(
            (Library.book_id == book_id) & (Library.user_id == str(user.id))
        )
        await redis.delete()
        await session.execute(stmt)
        await session.commit()
