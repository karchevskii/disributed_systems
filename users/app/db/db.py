from core.config import settings
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import text
import datetime
from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import (
    SQLAlchemyBaseOAuthAccountTableUUID,
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
class Base(DeclarativeBase):
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())"))
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=text(
        "TIMEZONE('utc', now())"), onupdate=datetime.datetime.utcnow)


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined"
    )




master_engine = create_async_engine(str(settings.DATABASE_MASTER_URI), pool_pre_ping=True)
replica_engine = create_async_engine(str(settings.DATABASE_REPLICA_URI), pool_pre_ping=True)

master_session_maker = async_sessionmaker(master_engine, expire_on_commit=False)
replica_session_maker = async_sessionmaker(replica_engine, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with master_session_maker() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)

# async def get_async_session(use_replica: bool = False) -> AsyncGenerator[AsyncSession, None]:
#     """Get a session from the master (default) or replica (if use_replica=True)."""
#     session_maker = replica_session_maker if use_replica else master_session_maker
#     async with session_maker() as session:
#         yield session


# async def get_user_db(session: AsyncSession = Depends(lambda: get_async_session(use_replica=False))):
#     yield SQLAlchemyUserDatabase(session, User, OAuthAccount)