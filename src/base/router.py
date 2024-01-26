from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Depends
from sqlalchemy import select, desc, asc
from sqlalchemy.sql.functions import count, func

from src.auth.base_config import current_optional_user
from src.database import async_session_maker
from src.library.models import Book

router = APIRouter(
    tags=['Base_page']
)

templates = Jinja2Templates(directory='src/templates')


@router.get('/')
async def get_base_page(request: Request, user=Depends(current_optional_user)):
    async with async_session_maker() as session:
        stmt = select(Book).limit(limit=10).where(Book.user_rating != 0).order_by(desc(Book.user_rating))

        stmt_scalars = await session.scalars(stmt)
        books = stmt_scalars.all()

    return templates.TemplateResponse(
        'base.html',
        {'request': request, 'user': user, 'books': books}
    )


@router.get('/test/')
async def stest():
    async with async_session_maker() as session:
        stmt = select(Book).limit(limit=10).where(Book.user_rating != 0).order_by(desc(Book.user_rating))

        stmt_scalars = await session.scalars(stmt)
        books = stmt_scalars.all()
    return [x.as_dict()['url_orig'] for x in books]
