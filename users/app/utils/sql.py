from abc import ABC, abstractmethod

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)

class AbstractSQLRepository(ABC):
    @abstractmethod
    async def add_one():
        raise NotImplementedError

    @abstractmethod
    async def edit_one():
        raise NotImplementedError

    @abstractmethod
    async def find_one():
        raise NotImplementedError

    @abstractmethod
    async def find_all():
        raise NotImplementedError

    @abstractmethod
    async def delete_one():
        raise NotImplementedError

    @abstractmethod
    async def delete_all():
        raise NotImplementedError

    @abstractmethod
    async def delete_all_by():
        raise NotImplementedError

    @abstractmethod
    async def find_all_by():
        raise NotImplementedError


class SQLAlchemyRepository(AbstractSQLRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict) -> int:
        stmt = insert(self.model).values(**data).returning(self.model)
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def edit_one(self, id: int, data: dict) -> int:
        stmt = update(self.model).values(**data).filter_by(id=id).returning(self.model)
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def find_all(self):
        stmt = select(self.model)
        res = await self.session.execute(stmt)
        logger.debug("Result: %s", res)
        return res.scalars().all()

    async def find_one(self, **filter_by):
        logger.debug("Filter by: %s", filter_by)
        stmt = select(self.model).filter_by(**filter_by)
        res = await self.session.execute(stmt)
        logger.debug("Result: %s", res)
        return res.unique().scalar_one_or_none()

    async def delete_one(self, id: int) -> None:
        stmt = delete(self.model).filter_by(id=id)
        await self.session.execute(stmt)

    async def delete_all(self):
        stmt = delete(self.model)
        await self.session.execute(stmt)

    async def find_all_by(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def delete_all_by(self, **filter_by):
        stmt = delete(self.model).filter_by(**filter_by)
        await self.session.execute(stmt)