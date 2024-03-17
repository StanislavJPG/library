from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

import src.crud as base_crud
from src.database import RedisCache, get_async_session

router = APIRouter(prefix='/api/base', tags=['base'])


@router.get('/get_best_books')
async def get_best_books_api(session: AsyncSession = Depends(get_async_session)) -> dict:
    # Redis instance with value name
    redis = RedisCache('best_books_rating')

    if await redis.exist():
        data = await redis.get()
    else:
        books_for_rating = await base_crud.read_books_for_top_rating(session=session)
        # executing data with redis
        data = await redis.executor(data=books_for_rating, ex=120)

    return data

