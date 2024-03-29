from typing import Optional

from fastapi import APIRouter, Request, Query, Depends, HTTPException, Security
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates

from src.admin.router import admin_panel_api, search_specific_book_from_database_api
from src.auth.base_config import current_optional_user, current_optional_superuser
from src.base.router import get_best_books_api
from src.crud import delete_redis_cache_statement
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
                        top_books_rating=Depends(get_best_books_api)):
    return templates.TemplateResponse(
        'base.html',
        {'request': request, 'user': user, 'top_books_rating': top_books_rating}
    )


@router.get('/profile')
async def get_profile_page(request: Request, session: AsyncSession = Depends(get_async_session),
                           book_name: Optional[str] = None,
                           page: Optional[int] = 1,
                           user=Security(current_optional_user)):
    full_profile_info = await get_profile_api(session=session, book_name=book_name, page=page, user=user)

    return templates.TemplateResponse(
        'my_profile.html',
        {
         'request': request,
         'books_in_profile': full_profile_info['books_in_profile'],
         'page': full_profile_info['page'],
         'books_not_in_profile': full_profile_info['books_not_in_profile'],
         'library': full_profile_info['library'],
         'user': full_profile_info['user']
        }
    )


@router.get('/admin_panel', response_class=HTMLResponse)
async def admin_panel_page(request: Request, admin=Depends(current_optional_superuser),
                           page: Optional[int] = 1, book_title: Optional[str] = None,
                           session: AsyncSession = Depends(get_async_session)):
    if page > 0:
        await delete_redis_cache_statement('admin_panel')
    if admin:
        book = await search_specific_book_from_database_api(book_title=book_title, session=session)
        admin_api = await admin_panel_api(page=page, session=session)

        return templates.TemplateResponse(
            'admin.html',
            {'request': request, 'user': admin, 'requested_book': book,
             'books_request': admin_api['books_request'], 'page': admin_api['page']}
        )
    else:
        raise HTTPException(status_code=404)


@router.get('/logout', response_class=HTMLResponse)
async def logout_page(request: Request, user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'logout.html', {'request': request, 'user': user}
    )


@router.get('/login', response_class=HTMLResponse)
async def login_page(request: Request, user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'login.html', {'request': request, 'user': user}
    )


@router.get('/registration')
async def registration_page(request: Request, user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'registration.html', {'request': request, 'user': user}
    )
