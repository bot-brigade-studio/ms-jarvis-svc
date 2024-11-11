# app/api/v1/endpoints/example.py
from fastapi import APIRouter, Depends
from app.utils.response_handler import response
from app.core.exceptions import APIError
from app.schemas.response import Error

router = APIRouter()

@router.get("/success-example")
async def success_example():
    data = {"key": "value"}
    return response.success(
        data=data,
        message="Data retrieved successfully",
        meta={"total": 1}
    )

@router.get("/error-example")
async def error_example():
    # Using error_response directly
    return response.error(
        message="Something went wrong",
        errors=[
            Error(code="INVALID_INPUT", message="Invalid input provided", field="field_name")
        ]
    )

@router.get("/error-exception-example")
async def error_exception_example():
    # Using APIError exception
    raise APIError(
        message="Something went wrong",
        status_code=400,
        errors=[
            Error(code="INVALID_INPUT", message="Invalid input provided", field="field_name")
        ]
    )