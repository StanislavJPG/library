import base64

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy import select, update

from src.auth.base_config import current_user, current_optional_user
from src.auth.models import User
from src.database import async_session_maker
from src.library.models import Book

test_profile = APIRouter(
    tags=['Profile_test']
)


@test_profile.get('/test')
async def view_books(book: str = None, user=Depends(current_optional_user)):
    if user:
        async with async_session_maker() as session:
            select_book = select(Book).where(Book.owner_id == str(user.id))
            current_user_book = await session.scalars(select_book)
            all_books_info_from_db = current_user_book.all()

            try:
                if [x.as_dict() for x in all_books_info_from_db][0]['owner_id']:
                    if book is None:
                        return all_books_info_from_db
                    else:
                        stmt = [x.as_dict() for x in all_books_info_from_db if x.as_dict()['title'] == book]
                    return stmt
            except IndexError:
                return []
