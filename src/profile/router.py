from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy import select, delete
from fastapi import status

from src.auth.base_config import current_active_user, current_user
from src.base.router import templates
from src.database import async_session_maker
from src.library.models import Book
from src.profile.service import view_books

router = APIRouter(
    tags=['MyProfile_page']
)


@router.get('/profile')
async def get_profile_page(request: Request, books=Depends(view_books),
                           user=Depends(current_active_user)):

    return templates.TemplateResponse(
        'my_profile.html',
        {'request': request, 'books': books, 'user': user}
    )


@router.delete('/books/{book_title}')
async def delete_book_from_profile(book_title: str, user=Depends(current_user)):
    async with async_session_maker() as session:
        try:
            select_book = select(Book).where(Book.owner_id == str(user.id))
            curr_user = await session.scalars(select_book)
            result = curr_user.all()
            if book_title in [x.as_dict()['title'] for x in result]:
                stmt = delete(Book).where(book_title == Book.title)
                await session.execute(stmt)
                await session.commit()
                raise HTTPException(status_code=200,
                                    detail={'success': status.HTTP_200_OK})
            raise HTTPException(status_code=404,
                                detail={'error': status.HTTP_404_NOT_FOUND})
        except AttributeError:
            raise HTTPException(status_code=401,
                                detail={'error': status.HTTP_401_UNAUTHORIZED})
