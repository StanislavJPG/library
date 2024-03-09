from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_optional_user, current_user
from src.crud import update_book_back_to_the_profile
from src.database import get_async_session
from src.profile.service import view_profile_information, delete_book, view_books

router = APIRouter(
    prefix='/api',
    tags=['profile']
)


@router.get('/profile')
async def get_profile_api(session: AsyncSession = Depends(get_async_session), book_name: Optional[str] = None,
                          page: Optional[int] = 1, user=Depends(current_user)) -> dict:
    profile_data = await view_profile_information(session, user)
    books_in_profile = await view_books(session=session, book_name=book_name, page=page, user=user)

    return {'books_in_profile': books_in_profile['books'],
            'page': books_in_profile['page'],
            'books_not_in_profile': profile_data['books'], 'profile_image': profile_data['image'],
            'library': profile_data['library']}


@router.delete('/books/{book_id}')
async def delete_book_from_profile_api(book_id: int, session: AsyncSession = Depends(get_async_session),
                                       user=Depends(current_optional_user)) -> None:
    await delete_book(book_id=book_id, session=session, user=user)


@router.put('/save_back/{book_id}')
async def save_book_back_to_profile_api(book_id: int, user=Depends(current_optional_user),
                                        session: AsyncSession = Depends(get_async_session)) -> None:
    """
    endpoint for change is_saved_to_profile to True (to save book to the profile)
    """
    await update_book_back_to_the_profile(session=session, book_id=book_id, user=user)
