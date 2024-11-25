from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.response import Error

class APIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        errors: list[Error] = None
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors
        super().__init__(self.message)

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
            "meta": None,
            "errors": [error.model_dump() for error in exc.errors] if exc.errors else None
        }
    )

async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        Error(
            code="VALIDATION_ERROR",
            message=f"{error['msg']}",
            field=str(error["loc"][-1])
        )
        for error in exc.errors()
    ]
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "data": None,
            "meta": None,
            "errors": [error.model_dump() for error in errors]
        }
    )

async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Database error",
            "data": None,
            "meta": None,
            "errors": [
                {
                    "code": "DATABASE_ERROR",
                    "message": str(exc),
                    "field": None
                }
            ]
        }
    )