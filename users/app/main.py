from fastapi import Depends, FastAPI

from app.oauth_route import get_oauth_router
from app.db import User
from app.core.config import settings
from app.schemas import UserRead, UserUpdate
from app.users import (
    auth_backend,
    current_active_user,
    fastapi_users,
    github_oauth_client,
)
from app.exceptions.handlers import all_exception_handlers

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(
    get_oauth_router(oauth_client=github_oauth_client,
                                   backend=auth_backend,
                                   state_secret=settings.SECRET,
                                   redirect_url=settings.CALLBACK_URL,
                                   get_user_manager=fastapi_users.get_user_manager,
                                   is_verified_by_default=True),
    prefix="/auth/github",
    tags=["auth"],
)


@app.get("/auth/check-auth")
async def check_auth(user: User = Depends(current_active_user)):
    return {"authenticated": True}

@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

for exc, handler in all_exception_handlers.items():
    app.add_exception_handler(exc, handler)