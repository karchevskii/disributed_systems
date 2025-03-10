import datetime
from typing import Annotated

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings

engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI), pool_pre_ping=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


created_at = Annotated[datetime.datetime, mapped_column(
    server_default=text("TIMEZONE('utc', now())"))]
updated_at = Annotated[datetime.datetime, mapped_column(
    server_default=text("TIMEZONE('utc', now())"),
    onupdate=datetime.datetime.utcnow,
)]

class Base(DeclarativeBase):
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


async def get_async_session():
    async with async_session_maker() as session:
        yield session