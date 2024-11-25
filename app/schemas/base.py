from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class BaseSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True