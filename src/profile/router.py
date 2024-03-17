from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_optional_user, current_user
import src.crud as base_crud
from src.database import get_async_session
from src.profile.service import view_books_not_in_profile, delete_book, view_paginated_books, view_profile_info

router = APIRouter(
    prefix='/api',
    tags=['profile']
)


@router.get('/profile')
async def get_profile_api(session: AsyncSession = Depends(get_async_session), book_name: Optional[str] = None,
                          page: Optional[int] = 1, user=Depends(current_user)) -> dict:
    books_not_in_profile = await view_books_not_in_profile(session, user)
    books_in_profile = await view_paginated_books(session=session, book_name=book_name, page=page, user=user)
    user_info = await view_profile_info(user=user)

    return {'books_in_profile': books_in_profile['books'],
            'page': books_in_profile['page'],
            'books_not_in_profile': books_not_in_profile['books_not_in_profile'],
            'user': user_info,
            'library': books_not_in_profile['library']}


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
    await base_crud.update_book_back_to_the_profile(session=session, book_id=book_id, user=user)
