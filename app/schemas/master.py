from pydantic import BaseModel


class MstCategoryBase(BaseModel):
    name: str
    slug: str


class MstItemBase(BaseModel):
    name: str
    description: str
