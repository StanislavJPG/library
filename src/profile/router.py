from typing import Optional

from fastapi import APIRouter, Request, Depends
from src.auth.base_config import current_optional_user
from src.base.router import templates
from src.profile.service import view_books, view_profile, delete_book

router = APIRouter(
    tags=['MyProfile_page']
)


@router.get('/profile')
async def get_profile_page(request: Request, book_name: Optional[str] = None,
                           user=Depends(current_optional_user),
                           profile_data=Depends(view_profile)):

    books_in_profile = await view_books(book_name, user)

    return templates.TemplateResponse(
        'my_profile.html',
        {'request': request, 'books_in_profile': books_in_profile,
         'books_not_in_profile': profile_data[0], 'user': user,
         'profile_image': profile_data[1], 'library': profile_data[2]}
    )


@router.delete('/books/{book_id}')
async def delete_book_from_profile(book_id: int, user=Depends(current_optional_user)):
    await delete_book(book_id, user)



