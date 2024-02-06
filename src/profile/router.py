from typing import Optional
from fastapi import APIRouter, Request, Depends
from src.auth.base_config import current_optional_user
from src.base.router import templates
from src.profile.service import view_profile_information, delete_book, view_books

router = APIRouter(
    tags=['profile_page']
)


@router.get('/profile')
async def get_profile_page(request: Request, book_name: Optional[str] = None,
                           page: Optional[int] = 1, user=Depends(current_optional_user),
                           profile_data=Depends(view_profile_information)):

    books_in_profile = await view_books(book_name, page, user)

    return templates.TemplateResponse(
        'my_profile.html',
        {'request': request, 'books_in_profile': books_in_profile['books'],
         'page': books_in_profile['page'],
         'books_not_in_profile': profile_data['books'], 'user': user,
         'profile_image': profile_data['image'], 'library': profile_data['library']}
    )


@router.delete('/books/{book_id}')
async def delete_book_from_profile(book_id: int, user=Depends(current_optional_user)):
    await delete_book(book_id, user)
