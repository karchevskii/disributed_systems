from app.api.routers.users import router as users_router
from app.api.routers.auth import router as auth_router

all_routers = [
    users_router,
    auth_router
]