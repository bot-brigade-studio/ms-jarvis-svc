from fastapi import APIRouter
from app.api.v1.endpoints import bot

api_router = APIRouter()

api_router.include_router(bot.router, prefix="/bot", tags=["bots"])