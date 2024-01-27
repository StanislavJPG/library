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
                        # print([x.as_dict() for x in all_books_info_from_db])
                        return all_books_info_from_db
                    else:
                        stmt = [x.as_dict() for x in all_books_info_from_db if x.as_dict()['title'] == book]
                    return stmt
            except IndexError:
                return []


async def get_user_image(image: UploadFile = File(...), user=Depends(current_user)):
    image_content = await image.read()
    image_url = f"data:image/{image.content_type.split('/')[1]};base64,{base64.b64encode(image_content).decode()}"

    async with async_session_maker() as session:
        stmt = update(User).where(User.id == str(user.id)).values(profile_image=image_url)
        await session.execute(stmt)
        await session.commit()
        return {'Success': 200}
