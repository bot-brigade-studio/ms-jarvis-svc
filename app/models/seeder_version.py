from sqlalchemy import Column, String, DateTime
from app.db.base import Base
import datetime


class SeederVersion(Base):
    __tablename__ = "seeder_versions"

    version_num = Column(String, primary_key=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
