from abc import ABC, abstractmethod
from typing import Type

from app.db.db import async_session_maker
from app.repos.users import UsersRepository


class IUnitOfWork(ABC):
    users: Type[UsersRepository]

    @abstractmethod
    def __init__(self):
        return NotImplementedError

    @abstractmethod
    async def __aenter__(self):
        return NotImplementedError

    @abstractmethod
    async def __aexit__(self, *args):
        return NotImplementedError

    @abstractmethod
    async def commit(self):
        return NotImplementedError

    @abstractmethod
    async def rollback(self):
        return NotImplementedError


class UnitOfWork:
    def __init__(self):
        self.session_factory = async_session_maker

    async def __aenter__(self):
        self.session = self.session_factory()

        self.users = UsersRepository(self.session)

    async def __aexit__(self, *args):
        await self.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()