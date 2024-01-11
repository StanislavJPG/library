from fastapi import APIRouter, Request, Query, Depends

from src.auth.base_config import current_user
from src.base.router import templates
from src.database import async_session_maker
from src.library.service import modified_take_book, get_full_info, save_book_database, get_urls_info, \
    get_title_info, specific_search

router = APIRouter(
    tags=['Library_page']
)


@router.get('/library')
async def get_library_page(request: Request,
                           user=Depends(current_user)):
    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'user': user}
    )


@router.get('/library/{literature}')
async def library_search(request: Request, literature: str,
                           user=Depends(current_user)):
    book_result = await specific_search(literature)
    author_result = await get_full_info(literature)

    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'book': book_result,
         'author_result': author_result, 'user_title': literature,
         'user': user})


@router.post('/library/save_book/{literature}')
async def save_book_page(request: Request, literature: str,
                         num: int = Query(..., description='Number'),
                         user=Depends(current_user)):
    database = await save_book_database(literature, num, user)

    return templates.TemplateResponse(
        'library.html',
        {'request': request, 'user_title': literature,
         'database': database, 'user': user}
    )


@router.get('/read/{literature}')
async def get_read_page(request: Request, literature: str,
                        num: int = Query(..., description='Number')):
    url = await get_urls_info(literature)
    title = await get_title_info(literature)

    return templates.TemplateResponse(
        'reader.html',
        {'request': request,
         'book': url[num % len(url)], 'title': [title, num+1],
         'num': num}
    )
