from typing import TypeVar, Generic, Sequence
from fastapi import Query
from pydantic import BaseModel
from sqlalchemy.orm import Query as SQLAlchemyQuery

T = TypeVar("T")

class PaginationParams(BaseModel):
    page: int = Query(1, ge=1, description="Page number")
    page_size: int = Query(10, ge=1, le=100, description="Items per page")

class PaginatedResult(Generic[T]):
    def __init__(self, items: Sequence[T], total: int, params: PaginationParams):
        self.items = items
        self.total = total
        self.page = params.page
        self.page_size = params.page_size
        self.total_pages = (total + params.page_size - 1) // params.page_size

def paginate_query(query: SQLAlchemyQuery, params: PaginationParams) -> PaginatedResult:
    total = query.count()
    items = query.offset((params.page - 1) * params.page_size).limit(params.page_size).all()
    return PaginatedResult(items=items, total=total, params=params)
