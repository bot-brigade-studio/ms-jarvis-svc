from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import (
    APIError,
    api_error_handler,
    validation_error_handler,
    sqlalchemy_error_handler,
)
from app.api.v1.router import api_router
from app.utils.response_handler import response
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.audit import AuditLogMiddleware
from app.middleware.context import ContextMiddleware


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        redirect_slashes=False,
        docs_url=f"{settings.ROOT_PATH}/docs",
        redoc_url=None,
    )

    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(AuditLogMiddleware)
    application.add_middleware(ContextMiddleware)
    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add exception handlers
    application.add_exception_handler(APIError, api_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)

    # Add routers
    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.get(f"{settings.ROOT_PATH}/")
    async def root():
        return response.success(
            data={"message": "Hello World"}, message="Welcome to the API"
        )

    # Add health check endpoint
    @application.get(f"{settings.ROOT_PATH}/health")
    async def health_check():
        return response.success(
            data={"status": "healthy"}, message="Service is healthy"
        )

    return application


app = create_application()
