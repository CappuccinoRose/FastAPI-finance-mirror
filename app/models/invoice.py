# app/models/invoice.py
from uuid import uuid4
from sqlalchemy import String, TEXT, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base

class Invoice(Base):
    __tablename__ = "invoices"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=uuid4)
    id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    owner_guid: Mapped[str] = mapped_column(String(36), nullable=False) # Assuming owner is an employee or vendor
    customer_guid: Mapped[str | None] = mapped_column(String(36), ForeignKey("customers.guid", ondelete="RESTRICT"))
    post_txn: Mapped[str | None] = mapped_column(String(36), ForeignKey("transactions.guid", ondelete="SET NULL"))
    date_posted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(TEXT)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="invoices")
    post_transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="invoices")
    entries: Mapped[list["Entry"]] = relationship("Entry", back_populates="invoice", cascade="all, delete-orphan", passive_deletes=True)

