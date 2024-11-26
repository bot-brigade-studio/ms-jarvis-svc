# app/database/seeder_registry.py
import os
from typing import List, Type
from app.database.seeders.base_seeder import BaseSeeder
from app.database.seeders.versions.v1_master_data import V1MasterData


class SeederRegistry:
    _seeders: List[Type[BaseSeeder]] = [V1MasterData]

    @classmethod
    def get_all_seeders(cls) -> List[BaseSeeder]:
        return [seeder() for seeder in cls._seeders]
