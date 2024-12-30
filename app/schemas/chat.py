from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class CreateThreadRequest(BaseModel):
    name: str


class CreateMessageRequest(BaseModel):
    content: str
    id: Optional[str] = None
    parent_id: Optional[str] = None
    response_id: Optional[str] = None
    team_id: Optional[str] = None
