# app/models/transaction.py
from uuid import uuid4
from sqlalchemy import String, TEXT, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base

# 为了避免循环导入，使用 TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.purchase_bill import PurchaseBill
    from app.models.split import Split
    from app.models.invoice import Invoice

class Transaction(Base):
    __tablename__ = "transactions"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=uuid4)
    post_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    enter_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT)
    source_purchase_bill: Mapped["PurchaseBill"] = relationship(
        "PurchaseBill", back_populates="posted_transaction"
    )
    splits: Mapped[list["Split"]] = relationship("Split", back_populates="transaction", cascade="all, delete-orphan", passive_deletes=True)
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="post_transaction")
