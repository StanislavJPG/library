from typing import Optional

from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from src.admin.router import admin_panel_api
from src.auth.base_config import current_optional_user, current_optional_superuser, current_superuser
from src.base.service import get_best_books
from src.library.router import library_search_api, get_read_page_api
from src.profile.router import get_profile_api
from src.profile.service import view_profile_information

router = APIRouter(
    tags=['Pages']
)

templates = Jinja2Templates(directory='src/templates')


@router.get('/library', response_class=HTMLResponse)
async def get_library_page(request: Request,
                           user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'user': user}
    )


@router.get('/library/{literature}', response_class=HTMLResponse)
async def library_search(request: Request, literature: str,
                         user=Depends(current_optional_user)):
    book = await library_search_api(literature=literature, user=user)

    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'book': book['book'], 'user_title': literature,
         'user': user, 'error': book['error']})


@router.get('/read/{literature}', response_class=HTMLResponse)
async def get_read_page(request: Request, literature: str,
                        num: int = Query(..., description='Number', gt=0),
                        user=Depends(current_optional_user)):
    book = await get_read_page_api(literature, num, user)

    return templates.TemplateResponse(
        'reader.html',
        {'request': request,
         'book': book['book'], 'title': literature.title(), 'num': num, 'user': user, 'rating': book['rating']}
    )


@router.get('/', response_class=HTMLResponse)
async def get_base_page(request: Request, user=Depends(current_optional_user),
                        top_books_rating=Depends(get_best_books)):
    return templates.TemplateResponse(
        'base.html',
        {'request': request, 'user': user, 'books': top_books_rating['books'],
         'library': top_books_rating['library']}
    )


@router.get('/profile', response_class=HTMLResponse)
async def get_profile_page(request: Request, book_name: Optional[str] = None,
                           page: Optional[int] = 1, user=Depends(current_optional_user),
                           admin=Depends(current_optional_superuser),
                           profile_data=Depends(view_profile_information)):

    all_books_info = await get_profile_api(book_name, page, user, profile_data)

    return templates.TemplateResponse(
        'my_profile.html',
        {'request': request, 'books_in_profile': all_books_info['books_in_profile'],
         'page': all_books_info['page'],
         'books_not_in_profile': all_books_info['books_not_in_profile'], 'user': user,
         'profile_image': all_books_info['profile_image'], 'library': all_books_info['library'],
         'admin': admin}
    )


@router.get('/admin_panel', response_class=HTMLResponse)
async def admin_panel_page(request: Request, admin=Depends(current_superuser),
                           page: Optional[int] = 1):
    admin_api = await admin_panel_api(page)

    return templates.TemplateResponse(
        'admin.html',
        {'request': request, 'admin': admin,
         'books_request': admin_api['books_request'], 'page': admin_api['page']}
    )
