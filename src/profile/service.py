from fastapi import APIRouter, Depends
from sqlalchemy import select

from src.auth.base_config import current_active_user
from src.database import async_session_maker
from src.library.models import Book

test_profile = APIRouter(
    tags=['Profile_test']
)


async def view_books(book: str = None, user=Depends(current_active_user)):
    async with async_session_maker() as session:
        select_book = select(Book).where(Book.owner_id == str(user.id))
        current_user_book = await session.scalars(select_book)
        result = current_user_book.all()
        try:
            if [x.as_dict() for x in result][0]['owner_id']:
                if book is None:
                    return result
                else:
                    stmt = [x.as_dict() for x in result if x.as_dict()['title'] == book]
                return stmt
        except IndexError:
            return []
