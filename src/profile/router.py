from fastapi import APIRouter, Request, Depends

from src.auth.base_config import current_active_user
from src.base.router import templates
from src.profile.service import view_books

router = APIRouter(
    tags=['MyProfile_page']
)


@router.get('/profile')
async def get_profile_page(request: Request, books=Depends(view_books),
                           user=Depends(current_active_user)):
    return templates.TemplateResponse(
        'my_profile.html',
        {'request': request, 'books': books, 'user': user}
    )


# @router.get('/profile/all_books')
# async def get_all_books(request: Request, books=Depends(view_books),
#                         user=Depends(current_active_user)):
#     return templates.TemplateResponse(
#         'my_profile.html',
#         {'request': request, 'books': books, 'user': user}
#     )
