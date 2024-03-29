from typing import Union, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from . import crud as admin_crud
from src.library.models import Book
from fastapi import APIRouter, HTTPException

test = APIRouter()


class AdminPanel:
    """
    class for taking a books that need to change by users requests
    """
    def __init__(self, page: int = 1) -> None:
        self.page = page

    async def get_users_requests(self, session: AsyncSession) -> Union[HTTPException, Sequence[Book]]:
        if self.page > 0:
            offset = (self.page - 1) * 4
        else:
            raise HTTPException(status_code=403, detail={'Error': 'Forbidden'})

        books = await admin_crud.read_requested_books_for_admin(session=session, offset=offset)
        return books
