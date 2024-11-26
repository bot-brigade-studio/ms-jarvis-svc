# app/database/seeders/base_seeder.py
from abc import ABC, abstractmethod
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.models.seeder_version import SeederVersion


class BaseSeeder(ABC):
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description

    @abstractmethod
    async def seed(self, session: AsyncSession) -> None:
        pass

    @abstractmethod
    async def unseed(self, session: AsyncSession) -> None:
        pass

    async def mark_as_seeded(self, session: AsyncSession) -> None:
        version = SeederVersion(
            version_num=self.version,
            description=self.description,
            created_at=datetime.now(),
        )
        session.add(version)
        await session.commit()

    async def mark_as_unseeded(self, session: AsyncSession) -> None:
        await session.execute(
            delete(SeederVersion).where(SeederVersion.version_num == self.version)
        )
        await session.commit()
