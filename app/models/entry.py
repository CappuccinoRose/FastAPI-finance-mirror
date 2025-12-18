# app/models/entry.py
from uuid import uuid4
from sqlalchemy import String, TEXT, ForeignKey, Integer, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from datetime import datetime

from app.db.base import Base

class Entry(Base):
    __tablename__ = "entries"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=uuid4)
    invoice_guid: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.guid", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(TEXT, nullable=False)
    action: Mapped[str | None] = mapped_column(String(50))
    account_guid: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.guid", ondelete="RESTRICT"), nullable=False)
    quantity_num: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_denom: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0.00)
    discounted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="entries")
    account: Mapped["Account"] = relationship("Account")
