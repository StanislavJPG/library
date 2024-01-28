from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Depends
from sqlalchemy import select, asc

from src.auth.base_config import current_optional_user
from src.database import async_session_maker
from src.library.models import BookRating

router = APIRouter(
    tags=['Base_page']
)

templates = Jinja2Templates(directory='src/templates')


@router.get('/')
async def get_base_page(request: Request, user=Depends(current_optional_user)):
    async with (async_session_maker() as session):
        stmt = select(BookRating
                      ).order_by(asc(BookRating.rating)
                                 ).where((BookRating.rating / BookRating.rating_count) >= 1).limit(10)
        stmt_scalars = await session.scalars(stmt)
        ratings_or_books = stmt_scalars.all()

    return templates.TemplateResponse(
        'base.html',
        {'request': request, 'user': user, 'books': ratings_or_books,
         'ratings': ratings_or_books}
    )
