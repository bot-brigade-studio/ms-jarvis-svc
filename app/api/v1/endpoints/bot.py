from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from app.api.v1.endpoints.deps import CurrentUser, get_current_user
from app.models.enums import StatusEnum
from app.services.bot import BotService
from app.schemas.bot import BotConfigCreate, BotConfigResponse, BotCreate, BotResponse
from app.utils.response_handler import response
from app.schemas.response import StandardResponse
from uuid import UUID

router = APIRouter()


@router.post("", response_model=StandardResponse[BotResponse])
async def create_bot(
    schema: BotCreate,
    service: BotService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    item = await service.create_bot(schema)

    return response.success(data=item, message="Bot created successfully")


@router.get("", response_model=StandardResponse[List[BotResponse]])
async def get_bots(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    status: Optional[StatusEnum] = Query(None),
    service: BotService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
    team_id: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
):
    joins = []
    filters = {}
    if status:
        filters["status"] = status
    if team_id:
        filters["team_access.team_id"] = team_id
        joins.append("team_access")
    
    search_fields = {"name": "contains"}
    search_term = None
    if name:
        search_term = name
        
    items, total = await service.get_bots(
        skip=skip,
        limit=limit, 
        filters=filters, 
        joins=joins, 
        search_term=search_term, 
        search_fields=search_fields
    )

    return response.success(
        data=items, message="Bots fetched successfully", meta={"total": total}
    )


@router.get("/{id}", response_model=StandardResponse[BotResponse])
async def get_bot(
    id: UUID,
    service: BotService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    item = await service.get_bot(id)

    return response.success(data=item, message="Bot fetched successfully")


@router.put("/{id}", response_model=StandardResponse[BotResponse])
async def update_bot(
    id: UUID,
    schema: BotCreate,
    service: BotService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    item = await service.update_bot(id, schema)

    return response.success(data=item, message="Bot updated successfully")


@router.delete("/{id}", response_model=StandardResponse[None])
async def delete_bot(
    id: UUID,
    service: BotService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    await service.delete_bot(id)

    return response.success(message="Bot deleted successfully")


@router.post("/{id}/configs", response_model=StandardResponse[BotConfigResponse])
async def create_bot_config(
    id: UUID,
    schema: BotConfigCreate,
    service: BotService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    item = await service.create_bot_config(id, schema)

    return response.success(data=item, message="Bot config created successfully")


@router.put(
    "/{id}/configs/{config_id}", response_model=StandardResponse[BotConfigResponse]
)
async def update_bot_config(
    id: UUID,
    config_id: UUID,
    schema: BotConfigCreate,
    service: BotService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    item = await service.update_bot_config(id, config_id, schema)

    return response.success(data=item, message="Bot config updated successfully")


@router.put(
    "/{id}/configs/{config_id}/is-current", response_model=StandardResponse[None]
)
async def update_bot_config_is_current(
    id: UUID,
    config_id: UUID,
    service: BotService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    await service.update_bot_config_is_current(id, config_id)

    return response.success(message="Bot config is current updated successfully")


@router.delete("/configs/{id}", response_model=StandardResponse[None])
async def delete_bot_config(
    id: UUID,
    service: BotService = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
):
    await service.delete_bot_config(id)

    return response.success(message="Bot config deleted successfully")
