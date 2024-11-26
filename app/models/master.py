from sqlalchemy import Column, ForeignKey
from app.models.base import SoftDeleteModel
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Index
from sqlalchemy.orm import relationship


class MstCategory(SoftDeleteModel):
    __tablename__ = "mst_categories"

    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True)


class MstItem(SoftDeleteModel):
    __tablename__ = "mst_items"

    category_id = Column(UUID(as_uuid=True), ForeignKey("mst_categories.id"))
    name = Column(String(255), nullable=False)
    description = Column(String(255))

    # Relationships
    bot_categories = relationship("Bot", back_populates="category")

    # index category_id and name
    __table_args__ = (Index("idx_category_id_name", category_id, name),)
