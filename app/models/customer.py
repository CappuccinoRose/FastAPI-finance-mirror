# app/models/customer.py
from sqlalchemy import String, TEXT, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4

from app.db.base import Base

class Customer(Base):
    __tablename__ = "customers"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    id: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(TEXT)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="customer")

