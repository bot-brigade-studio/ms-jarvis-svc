from app.core.repository import BaseRepository
from app.models.master import MstCategory, MstItem


class MstCategoryRepository(BaseRepository[MstCategory, None, None]):
    pass


class MstItemRepository(BaseRepository[MstItem, None, None]):
    pass
