from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from src.core.db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(200), nullable=False, index=True)
    company = Column(String(200), nullable=False)
    position = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    salary = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

