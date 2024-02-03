from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Depends
from sqlalchemy import update

from src.auth.base_config import current_optional_user
from src.base.service import get_top_books
from src.database import async_session_maker
from src.library.models import Library

router = APIRouter(
    tags=['Base_page']
)

templates = Jinja2Templates(directory='src/templates')


@router.get('/')
async def get_base_page(request: Request, user=Depends(current_optional_user),
                        top_books_rating=Depends(get_top_books)):
    return templates.TemplateResponse(
        'base.html',
        {'request': request, 'user': user, 'books': top_books_rating[0],
         'library': top_books_rating[1]}
    )


@router.put('/save_back/{book_id}')    # endpoint for change is_saved_to_profile to True (to save book to the profile)
async def save_book_back_to_profile(book_id: int,
                                    user=Depends(current_optional_user)):
    async with async_session_maker() as session:
        stmt = update(Library).values(is_saved_to_profile=True).where(
            (Library.book_id == book_id) & (Library.user_id == str(user.id))
        )
        await session.execute(stmt)
        await session.commit()

