from fastapi import APIRouter
from app.api.v1.endpoints import bot, master, file, chat

api_router = APIRouter()

api_router.include_router(bot.router, prefix="/bots", tags=["bots"])
api_router.include_router(master.router, prefix="/masters", tags=["masters"])
api_router.include_router(file.router, prefix="/files", tags=["files"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
