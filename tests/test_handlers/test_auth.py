from sqlalchemy import insert, select, text

from tests.conftest import test_async_session_maker


async def test_get_user_from_database():
    async with test_async_session_maker() as session:
        stmt = text(f"INSERT INTO public.user VALUES ('s', 's', 'aa9eb94f-0b3f-402d-80cc-36b32d27d225', 's', 's', true, false, false)")
        await session.execute(stmt)
        await session.commit()



