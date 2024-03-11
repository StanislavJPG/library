from sqlalchemy import update, select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from src.library.models import Book
from src.library.shemas import BookCreate


async def update_book_args_by_admin(session: AsyncSession, book: BookCreate) -> None:
    stmt = await session.scalar(select(Book.id).where(Book.id == book.id))
    await session.execute(update(Book).values(
        title=book.title,
        image=book.image,
        description=book.description,
        url=book.url,
        url_orig=book.url_orig
    ).where(Book.id == int(stmt)))
    await session.commit()


async def read_specific_book_from_database_by_admin(session: AsyncSession, book_title: str = None) -> Book | None:
    if book_title:
        stmt = await session.scalar(select(Book).where(Book.title.like(f'%{book_title}%').__or__(
            Book.title.like(f'%{book_title.title()}%'))))
    else:
        return None
    return stmt


async def read_requested_books_for_admin(session: AsyncSession, offset: int) -> Sequence[Book]:
    stmt = await session.scalars(select(Book).where(
        (Book.title.isnot(None)) & (Book.image.isnot(None)) &
        (Book.url_orig.is_(None))).offset(offset).limit(4))
    return stmt.all()
