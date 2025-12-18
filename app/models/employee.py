# app/models/employee.py
from uuid import uuid4
from sqlalchemy import String, TEXT, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Employee(Base):
    __tablename__ = "employees"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    id: Mapped[str | None] = mapped_column(String(50))
    language: Mapped[str | None] = mapped_column(String(10))
    acl: Mapped[str | None] = mapped_column(TEXT)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
