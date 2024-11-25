from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.services.bot import BotService
from app.schemas.bot import BotCreate, BotResponse
from app.utils.response_handler import response
from app.schemas.response import StandardResponse
from uuid import UUID

router = APIRouter()

@router.post("", response_model=StandardResponse[BotResponse])
async def create_bot(schema: BotCreate, service: BotService = Depends()):
    item = await service.create_bot(schema)
    
    return response.success(
        data=item,
        message="Bot created successfully"
    )