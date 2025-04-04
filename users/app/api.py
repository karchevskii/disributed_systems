import contextlib
from fastapi import APIRouter
import uuid

from app.users import get_user_manager, auth_backend
from app.schemas import UserCreate
from app.db import get_async_session, get_user_db

router = APIRouter(
    prefix="/users-service/auth",
    tags=["auth"],
)

get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


@router.get("/users-service/create-guest")
async def create_guest():
    try:
        # random email with uuid
        email = f"{uuid.uuid4()}@guest.{uuid.uuid4()}.com"

        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreate(
                            email=email,
                            password="guest",
                            is_active=True,
                            is_verified=True
                        )
                    )
                    strategy = auth_backend.get_strategy()
                    response = await auth_backend.login(strategy, user)

        return {"message": "created"}
    except Exception as e:
        raise
