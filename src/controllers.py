from typing import Any
from sqlalchemy import select, insert, update, delete
from src.database import async_session_maker


class CRUD:
    """
    this is CRUD class, that includes all operations with database
    that is are related to optimize code and make it easier to read and use
    """
    def __init__(self, class_):
        self.class_ = class_

    async def read_args(self, conditions: Any, is_single_result: bool = None) -> Any:
        """
        is_single_result=True provides a scalar
        and is_single_result=False provides scalars(for taking many results)
        """
        statement = select(self.class_).where(conditions)

        async with async_session_maker() as session:
            async with session.begin():
                if is_single_result is True:
                    response = await session.scalar(statement)
                elif is_single_result is False:
                    response = await session.scalars(statement)
                else:
                    raise Exception('Use `is_single_result` argument to achieve amount of results')

                return response

    async def create_args(self, **data) -> Any:
        async with async_session_maker() as session:
            async with session.begin():
                await session.execute(
                    insert(self.class_).values(**data)
                )
                await session.commit()

    async def update_args(self, conditions: Any, **data) -> Any:
        async with async_session_maker() as session:
            async with session.begin():
                await session.execute(
                    update(self.class_).values(**data).where(conditions)
                )
                await session.commit()

    async def delete_args(self, conditions: Any) -> Any:
        async with async_session_maker() as session:
            async with session.begin():
                await session.execute(
                    delete(self.class_).where(conditions)
                )
                await session.commit()
