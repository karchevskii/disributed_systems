import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.db import Base


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, nullable=False)
    username: Mapped[str]
    authenticators = Mapped[List["AuthenticatorModel"]] = relationship(
        foreign_keys="[AuthenticatorModel.user_id]", back_populates="user",
        cascade="all, delete-orphan", passive_deletes=True
    )

class AuthenticatorModel(Base):
    __tablename__ = 'authenticator'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=False
    )
    provider_account_id: Mapped[str]
    credential_public_key: Mapped[str]
    counter: Mapped[int]
    credential_device_type: Mapped[str]
    credential_backed_up: Mapped[bool]
    transports: Mapped[str]

    user: Mapped["UserModel"] = relationship(
        foreign_keys=[user_id], back_populates='authenticators')

