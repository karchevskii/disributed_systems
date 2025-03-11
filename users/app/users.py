import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from httpx_oauth.clients.github import GitHubOAuth2
from fastapi_users import exceptions

from db.db import get_user_db, User
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


github_oauth_client = GitHubOAuth2(
    settings.GITHUB_OAUTH_CLIENT_ID,
    settings.GITHUB_OAUTH_CLIENT_SECRET,
    scopes=["read:user", "user:email"],
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET
    verification_token_secret = settings.SECRET

    # async def read_user(self, user_id: uuid.UUID, request_user: User):
    #     """Allow any authenticated user to view other users."""
    #     user = await self.user_db.get(user_id)
    #     if user is None:
    #         raise exceptions.UserNotExists()
    #     return user

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


cookie_transport = CookieTransport(cookie_max_age=604800) # 1 week


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(secret=settings.SECRET, lifetime_seconds=604800) # 1 week


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)