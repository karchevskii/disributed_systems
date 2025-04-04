from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

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
from app.api import router
from app.exceptions.handlers import all_exception_handlers

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/users-service/openapi.json",
    docs_url="/users-service/docs",
    redoc_url="/users-service/redoc"
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users-service/users",
    tags=["users"],
)
app.include_router(
    get_oauth_router(oauth_client=github_oauth_client,
                                   backend=auth_backend,
                                   state_secret=settings.SECRET,
                                   redirect_url=settings.CALLBACK_URL,
                                   get_user_manager=fastapi_users.get_user_manager,
                                   is_verified_by_default=True),
    prefix="/users-service/auth/github",
    tags=["auth"],
)
app.include_router(router)


@app.get("/users-service/auth/check-auth")
async def check_auth(user: User = Depends(current_active_user)):
    return {"authenticated": True}

@app.get("/users-service/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return RedirectResponse(url=settings.FRONTEND_URL)

@app.get("/users-service/auth/logout", tags=["auth"])
async def logout():
    response = {"message": "Logged out"}
    # Create a response object with message
    from fastapi.responses import JSONResponse
    response_obj = JSONResponse(content=response)
    # Delete the tictactoe cookie
    response_obj.delete_cookie(key="tictactoe", path="/")
    return response_obj

@app.get("/users-service/health")
async def health_check():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_URL,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

for exc, handler in all_exception_handlers.items():
    app.add_exception_handler(exc, handler)