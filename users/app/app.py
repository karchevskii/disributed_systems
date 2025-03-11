from fastapi import Depends, FastAPI

from oauth_route import get_oauth_router
from db.db import User
from core.config import settings
from schemas import UserCreate, UserRead, UserUpdate
from users import (
    auth_backend,
    current_active_user,
    fastapi_users,
    github_oauth_client,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

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
