from typing import Optional, Generic, TypeVar, Any
from pydantic import BaseModel

DataT = TypeVar("DataT")

class Error(BaseModel):
    code: str
    message: str
    field: Optional[str] = None

class Meta(BaseModel):
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    total_pages: Optional[int] = None

class StandardResponse(BaseModel, Generic[DataT]):
    success: bool
    message: str
    data: Optional[DataT] = None
    meta: Optional[Meta] = None
    errors: Optional[list[Error]] = None