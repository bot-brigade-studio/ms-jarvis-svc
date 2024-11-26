from app.database.seeders.base_seeder import BaseSeeder
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.master import MstCategory, MstItem
from datetime import datetime


class V1MasterData(BaseSeeder):
    def __init__(self):
        super().__init__(version="v1_master_data", description="Master data seeding")

    async def seed(self, session: AsyncSession) -> None:
        bot_category = MstCategory(
            name="Bot Category",
            slug="bot-category",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(bot_category)
        await session.flush()

        items = [
            "Finance",
            "Marketing",
            "Sales",
            "Engineering",
            "HR",
            "Legal",
            "Others",
            "Academy",
            "Recruitment",
            "IT",
            "Others",
        ]

        mst_items = [
            MstItem(
                name=item,
                category_id=bot_category.id,
                description="",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for item in items
        ]

        session.add_all(mst_items)
        await session.flush()
        await self.mark_as_seeded(session)

    async def unseed(self, session: AsyncSession) -> None:
        from sqlalchemy import delete

        # Remove seeded data
        await session.execute(delete(MstItem))
        await session.execute(delete(MstCategory))
        await session.commit()
        await self.mark_as_unseeded(session)
