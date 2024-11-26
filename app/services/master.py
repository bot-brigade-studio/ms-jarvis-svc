from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import APIError
from app.db.session import get_db
from app.models.master import MstCategory, MstItem
from app.repositories.master_repository import MstCategoryRepository, MstItemRepository
from app.schemas.master import MstCategoryBase, MstItemBase


class MasterService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.mst_category_repo = MstCategoryRepository(MstCategory, db)
        self.mst_item_repo = MstItemRepository(MstItem, db)

    async def create_mst_category(self, schema: MstCategoryBase) -> MstCategory:
        return await self.mst_category_repo.create(schema)

    async def update_mst_category(
        self, id: UUID, schema: MstCategoryBase
    ) -> MstCategory:
        existing = await self.mst_category_repo.get(
            filters={"id": id}, select_fields=["id"]
        )
        if not existing:
            raise APIError(status_code=404, message="MstCategory not found")

        return await self.mst_category_repo.update(id, schema)

    async def delete_mst_category(self, id: UUID) -> None:
        existing = await self.mst_category_repo.get(
            filters={"id": id}, select_fields=["id"]
        )
        if not existing:
            raise APIError(status_code=404, message="MstCategory not found")

        return await self.mst_category_repo.delete(id)

    async def get_mst_category(self, id: UUID) -> MstCategory:
        return await self.mst_category_repo.get(filters={"id": id})

    async def get_mst_categories(
        self, skip: int = 0, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[MstCategory], int]:
        return await self.mst_category_repo.get_multi(
            skip=skip, limit=limit, filters=filters
        )

    async def _get_category_id(self, slug: str) -> UUID:
        category = await self.mst_category_repo.get(
            filters={"slug": slug}, select_fields=["id"]
        )
        if not category:
            raise APIError(status_code=404, message="MstCategory not found")
        return category.id

    async def create_mst_item(self, slug: str, schema: MstItemBase) -> MstItem:
        category_id = await self._get_category_id(slug)
        return await self.mst_item_repo.create(
            {
                "category_id": category_id,
                **schema.model_dump(),
            }
        )

    async def update_mst_item(
        self, slug: str, id: UUID, schema: MstItemBase
    ) -> MstItem:
        category_id = await self._get_category_id(slug)
        existing = await self.mst_item_repo.get(
            filters={"id": id, "category_id": category_id}
        )
        if not existing:
            raise APIError(status_code=404, message="MstItem not found")

        return await self.mst_item_repo.update(id, schema)

    async def delete_mst_item(self, slug: str, id: UUID) -> None:
        category_id = await self._get_category_id(slug)
        existing = await self.mst_item_repo.get(
            filters={"id": id, "category_id": category_id}
        )
        if not existing:
            raise APIError(status_code=404, message="MstItem not found")

        return await self.mst_item_repo.delete(id)

    async def get_mst_item(self, id: UUID) -> MstItem:
        return await self.mst_item_repo.get(filters={"id": id})

    async def get_mst_items(
        self,
        slug: str,
        skip: int = 0,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[MstItem], int]:
        category_id = await self._get_category_id(slug)
        filters = filters or {}
        filters["category_id"] = category_id
        return await self.mst_item_repo.get_multi(
            skip=skip, limit=limit, filters=filters
        )
