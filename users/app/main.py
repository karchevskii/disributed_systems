from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import all_routers

app = FastAPI(

)

for router in all_routers:
    app.include_router(router)

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