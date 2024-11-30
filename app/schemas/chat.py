from pydantic import BaseModel


class CreateThreadRequest(BaseModel):
    name: str
