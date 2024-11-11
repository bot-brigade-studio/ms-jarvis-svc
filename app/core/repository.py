# app/core/repository.py
from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func
from pydantic import BaseModel
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    async def create(self, schema: CreateSchemaType) -> ModelType:
        db_obj = self.model(**schema.model_dump(exclude_unset=True))
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def get(self, id: Any) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict = None
    ) -> tuple[List[ModelType], int]:
        stmt = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)

        total = await self.db.scalar(select(func.count()).select_from(stmt))
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        
        return result.scalars().all(), total

    async def update(
        self,
        *,
        id: Any,
        schema: UpdateSchemaType
    ) -> Optional[ModelType]:
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**schema.model_dump(exclude_unset=True))
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.scalar_one_or_none()

    async def delete(self, *, id: Any) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.rowcount > 0