from typing import Any, Optional
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.schemas.response import Error, Meta
from datetime import datetime, date

class ResponseHandler:
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        meta: Optional[Meta] = None,
        status_code: int = 200,
    ) -> JSONResponse:
        """
        Create a success response with standardized format
        """
        response_data = {
            "success": True,
            "message": message,
            "data": jsonable_encoder(
                data,
                custom_encoder={
                    datetime: lambda dt: dt.isoformat(),
                    date: lambda d: d.isoformat(),
                }
            ),
            "meta": jsonable_encoder(meta) if meta else None,
            "errors": None
        }

        # Remove None values
        response_data = {k: v for k, v in response_data.items() if v is not None}

        return JSONResponse(
            content=response_data,
            status_code=status_code
        )

    @staticmethod
    def error(
        message: str = "Error",
        errors: Optional[list[Error]] = None,
        status_code: int = 400,
    ) -> JSONResponse:
        """
        Create an error response with standardized format
        """
        response_data = {
            "success": False,
            "message": message,
            "data": None,
            "meta": None,
            "errors": jsonable_encoder(errors) if errors else None
        }

        # Remove None values
        response_data = {k: v for k, v in response_data.items() if v is not None}

        return JSONResponse(
            content=response_data,
            status_code=status_code
        )

response = ResponseHandler()