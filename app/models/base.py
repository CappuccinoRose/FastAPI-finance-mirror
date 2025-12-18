# app/models/base.py
import uuid
from sqlalchemy import Column, String, DateTime, func
from app.db.base import Base

class BaseModel(Base):
    __abstract__ = True

    guid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
