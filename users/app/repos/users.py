from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.models import (
    UserModel,
)
from app.utils.sql import SQLAlchemyRepository


class UsersRepository(SQLAlchemyRepository):
    model = UserModel