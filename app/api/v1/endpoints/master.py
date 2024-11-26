from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from app.services.master import MasterService
from app.schemas.master import MstCategoryBase, MstItemBase
from app.utils.debug import debug_print
from app.utils.response_handler import response
from app.schemas.response import StandardResponse
from uuid import UUID

router = APIRouter()


@router.post("/categories", response_model=StandardResponse[MstCategoryBase])
async def create_mst_category(
    schema: MstCategoryBase, service: MasterService = Depends()
):
    item = await service.create_mst_category(schema)
    return response.success(
        data=item,
        message="MstCategory created successfully",
    )


@router.put("/categories/{id}", response_model=StandardResponse[MstCategoryBase])
async def update_mst_category(
    id: UUID, schema: MstCategoryBase, service: MasterService = Depends()
):
    item = await service.update_mst_category(id, schema)
    return response.success(
        data=item,
        message="MstCategory updated successfully",
    )


@router.get("/categories/{id}", response_model=StandardResponse[MstCategoryBase])
async def get_mst_category(id: UUID, service: MasterService = Depends()):
    item = await service.get_mst_category(id)
    return response.success(
        data=item,
        message="MstCategory fetched successfully",
    )


@router.get("/categories", response_model=StandardResponse[List[MstCategoryBase]])
async def get_mst_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    service: MasterService = Depends(),
):
    items, total = await service.get_mst_categories(skip, limit)
    return response.success(
        data=items,
        message="MstCategories fetched successfully",
        meta={"total": total},
    )


@router.delete("/categories/{id}", response_model=StandardResponse[None])
async def delete_mst_category(id: UUID, service: MasterService = Depends()):
    await service.delete_mst_category(id)
    return response.success(message="MstCategory deleted successfully")


@router.post("/categories/{slug}/items", response_model=StandardResponse[MstItemBase])
async def create_mst_item(
    slug: str, schema: MstItemBase, service: MasterService = Depends()
):
    item = await service.create_mst_item(slug, schema)
    return response.success(
        data=item,
        message="MstItem created successfully",
    )


@router.put(
    "/categories/{slug}/items/{id}", response_model=StandardResponse[MstItemBase]
)
async def update_mst_item(
    slug: str, id: UUID, schema: MstItemBase, service: MasterService = Depends()
):
    item = await service.update_mst_item(slug, id, schema)
    return response.success(data=item, message="MstItem updated successfully")


@router.delete("/categories/{slug}/items/{id}", response_model=StandardResponse[None])
async def delete_mst_item(slug: str, id: UUID, service: MasterService = Depends()):
    await service.delete_mst_item(slug, id)
    return response.success(message="MstItem deleted successfully")


@router.get(
    "/categories/{slug}/items/{id}", response_model=StandardResponse[MstItemBase]
)
async def get_mst_item(slug: str, id: UUID, service: MasterService = Depends()):
    item = await service.get_mst_item(id)
    return response.success(data=item, message="MstItem fetched successfully")


@router.get(
    "/categories/{slug}/items", response_model=StandardResponse[List[MstItemBase]]
)
async def get_mst_items(
    slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    service: MasterService = Depends(),
):
    items, total = await service.get_mst_items(slug, skip, limit)
    return response.success(
        data=items,
        message="MstItems fetched successfully",
        meta={"total": total},
    )
