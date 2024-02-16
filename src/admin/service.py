from sqlalchemy import select, update

from src.database import async_session_maker
from src.library.models import Book
from src.library.shemas import BookCreate
from fastapi import APIRouter

test = APIRouter()


class AdminPanel:
    @staticmethod
    async def get_users_requests():
        async with async_session_maker() as session:
            query = await session.scalars(select(Book.title).where(
                (Book.title.isnot(None)) & (Book.url_orig.is_(None)))
            )
            books = query.all()
        return books

    @staticmethod
    @test.post('/asf')
    async def create_book(book: BookCreate):
        pass
