from typing import Optional

from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates

from src.admin.router import admin_panel_api
from src.auth.base_config import current_optional_user, current_optional_superuser
from src.base.service import get_best_books
from src.database import get_async_session
from src.library.router import library_search_api, get_read_page_api
from src.profile.router import get_profile_api

router = APIRouter(
    tags=['Pages']
)

templates = Jinja2Templates(directory='src/templates')


@router.get('/library')
async def get_library_page(request: Request,
                           user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'user': user}
    )


@router.get('/library/{literature}')
async def library_search(request: Request, literature: str, session: AsyncSession = Depends(get_async_session),
                         user=Depends(current_optional_user)):
    book = await library_search_api(literature=literature, user=user, session=session)

    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'book': book['book'], 'user_title': literature,
         'user': user, 'error': book['error']})


@router.get('/read/{literature}')
async def get_read_page(request: Request, literature: str,
                        num: int = Query(..., description='Number', gt=0),
                        user=Depends(current_optional_user), session: AsyncSession = Depends(get_async_session)):
    book = await get_read_page_api(literature=literature, num=num, user=user, session=session)

    return templates.TemplateResponse(
        'reader.html',
        {'request': request,
         'book': book['book'], 'title': literature.title(), 'num': num, 'user': user, 'rating': book['rating']}
    )


@router.get('/')
async def get_base_page(request: Request, user=Depends(current_optional_user),
                        top_books_rating=Depends(get_best_books)):
    return templates.TemplateResponse(
        'base.html',
        {'request': request, 'user': user, 'books': top_books_rating['books'],
         'library': top_books_rating['library']}
    )


@router.get('/profile')
async def get_profile_page(request: Request, session: AsyncSession = Depends(get_async_session),
                           book_name: Optional[str] = None,
                           page: Optional[int] = 1, user=Depends(current_optional_user),
                           admin=Depends(current_optional_superuser)):
    all_books_info = await get_profile_api(session=session, book_name=book_name, page=page, user=user)

    return templates.TemplateResponse(
        'my_profile.html',
        {'request': request, 'books_in_profile': all_books_info['books_in_profile'], 'page': all_books_info['page'],
         'books_not_in_profile': all_books_info['books_not_in_profile'], 'user': user,
         'profile_image': all_books_info['profile_image'], 'library': all_books_info['library'],
         'admin': admin}
    )


@router.get('/admin_panel', response_class=HTMLResponse)
async def admin_panel_page(request: Request, admin=Depends(current_optional_superuser),
                           page: Optional[int] = 1, session: AsyncSession = Depends(get_async_session)):
    if admin:
        admin_api = await admin_panel_api(page, session=session)

        return templates.TemplateResponse(
            'admin.html',
            {'request': request, 'user': admin,
             'books_request': admin_api['books_request'], 'page': admin_api['page']}
        )
    else:
        raise HTTPException(status_code=404)
