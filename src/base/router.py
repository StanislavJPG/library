from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import update

from src.auth.base_config import current_optional_user
from src.base.service import get_best_books
from src.database import async_session_maker, RedisCash
from src.library.models import Library

router = APIRouter(
    tags=['base_page']
)

templates = Jinja2Templates(directory='src/templates')


@router.get('/', response_class=HTMLResponse)
async def get_base_page(request: Request, user=Depends(current_optional_user),
                        top_books_rating=Depends(get_best_books)):
    return templates.TemplateResponse(
        'base.html',
        {'request': request, 'user': user, 'books': top_books_rating['books'],
         'library': top_books_rating['library']}
    )


@router.put('/save_back/{book_id}', response_model=None)
async def save_book_back_to_profile(book_id: int, user=Depends(current_optional_user)):
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

