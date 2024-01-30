import base64

from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, delete, update
from fastapi import status

from src.auth.base_config import current_optional_user, current_user
from src.auth.models import User
from src.base.router import templates
from src.database import async_session_maker
from src.library.models import Book
from src.profile.service import view_books

router = APIRouter(
    tags=['MyProfile_page']
)


@router.get('/profile')
async def get_profile_page(request: Request, books=Depends(view_books),
                           user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'my_profile.html',
        {'request': request, 'books': books, 'user': user}
    )


@router.delete('/books/{book_title}')
async def delete_book_from_profile(book_title: str, user=Depends(current_optional_user)):
    async with async_session_maker() as session:
        try:
            stmt_check_is_has_rating = select(Book.user_rating).where(
                (Book.owner_id == str(user.id)) & (Book.title == book_title))
            is_has_rating = await session.scalars(stmt_check_is_has_rating)
            is_has_rating = is_has_rating.first()

            select_book = select(Book).where(Book.owner_id == str(user.id))
            curr_user = await session.scalars(select_book)
            result = curr_user.all()

            if is_has_rating is None:
                if book_title in [x.as_dict()['title'] for x in result]:
                    stmt = delete(Book).where(book_title == Book.title)
                else:
                    raise HTTPException(status_code=404,
                                        detail={'error': status.HTTP_404_NOT_FOUND})
            else:
                stmt = update(Book).values(saved_to_profile=False).where(
                    (Book.owner_id == str(user.id)) & (Book.title == book_title))

            await session.execute(stmt)
            await session.commit()
            raise HTTPException(status_code=200,
                                detail={'success': status.HTTP_200_OK})
        except AttributeError:
            raise HTTPException(status_code=401,
                                detail={'error': status.HTTP_401_UNAUTHORIZED})


@router.patch('/image')
async def get_user_image(image: UploadFile = File(...), user=Depends(current_user)):
    image_content = await image.read()
    image_url = f"data:image/{image.content_type.split('/')[1]};base64,{base64.b64encode(image_content).decode()}"

    async with async_session_maker() as session:
        stmt = update(User).where(User.id == str(user.id)).values(profile_image=image_url)
        await session.execute(stmt)
        await session.commit()
        return {'Success': 200}
