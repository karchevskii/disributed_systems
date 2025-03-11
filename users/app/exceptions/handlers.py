from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.exceptions import (
    AuthServiceError
)

async def user_service_error_exception_handler(request: Request, exc: AuthServiceError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder({"detail": str(exc)}),
    )


all_exception_handlers = {
    AuthServiceError: user_service_error_exception_handler
}