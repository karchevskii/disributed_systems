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

from app.db import get_user_db, User
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


github_oauth_client = GitHubOAuth2(
    settings.GITHUB_OAUTH_CLIENT_ID,
    settings.GITHUB_OAUTH_CLIENT_SECRET,
    scopes=["read:user", "user:email"],
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET
    verification_token_secret = settings.SECRET

    # def __init__(self,
    #              user_db: SQLAlchemyUserDatabase,
    #              user_read_only_db: SQLAlchemyUserDatabase
    #              ):
    #     # self.user_db = user_db
    #     self.user_read_only_db = user_read_only_db
    #     super().__init__(user_db)

    # async def get(self, id: models.ID) -> models.UP:
    #     """
    #     Get a user by id.

    #     :param id: Id. of the user to retrieve.
    #     :raises UserNotExists: The user does not exist.
    #     :return: A user.
    #     """
    #     print("id", id)
    #     user = None
    #     try:
    #         user = await self.user_db.get(id)
    #         print("main db")
    #     except Exception as e:
    #         if isinstance(e, OSError):
    #             print("OSError")
    #             # If a main db is down, try to get the user from the read-only db.
    #             try:
    #                 user = await self.user_read_only_db.get(id)
    #                 print("read only db")
    #             except Exception as e:
    #                 # The read-only db is also down.
    #                 print("read only db down")
    #                 raise AuthServiceError(
    #                     "We are experiencing technical difficulties. Please try again later.")

    #     if user is None:
    #         raise exceptions.UserNotExists()
    #     return user

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(
            f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(
            f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


cookie_transport = CookieTransport(
    cookie_name="tictactoe", cookie_max_age=604800, cookie_secure=False, cookie_domain=".localhost")  # 1 week


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    # 1 week
    return JWTStrategy(secret=settings.SECRET, lifetime_seconds=604800)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
