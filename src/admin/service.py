from typing import Union

from sqlalchemy import select

from src.database import async_session_maker
from src.library.models import Book
from fastapi import APIRouter, HTTPException

test = APIRouter()


class AdminPanel:
    """
    class for taking a books that need to change by users requests
    """
    def __init__(self, page: int = 1):
        self.page = page

    async def get_users_requests(self) -> Union[HTTPException, list]:
        if self.page > 0:
            offset = (self.page - 1) * 4
        else:
            raise HTTPException(status_code=403, detail={'Error': 'Forbidden'})

        async with async_session_maker() as session:
            query = await session.scalars(select(Book).where(
                (Book.title.isnot(None)) & (Book.image.isnot(None)) &
                (Book.url_orig.is_(None))).offset(offset).limit(4)
            )
            books = query.all()
        return books
