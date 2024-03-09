from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import read_books_for_top_rating
from src.database import RedisCache, get_async_session

router = APIRouter(prefix='/api', tags=['base'])


@router.get('/base/get_best_books')
async def get_best_books_api(session: AsyncSession = Depends(get_async_session)) -> dict:
    # Redis instance with value name
    redis = RedisCache('best_books_rating')
    is_cache_exists = await redis.check()

    if is_cache_exists:
        data = await redis.get()
    else:
        books_for_rating = await read_books_for_top_rating(session=session)
        # executing data with redis
        data = await redis.executor(data=books_for_rating, ex=40)

    return data
