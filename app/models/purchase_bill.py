# app/models/purchase_bill.py
import uuid
from sqlalchemy import String, Date, Text, DECIMAL, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.vendor import Vendor
    from app.models.transaction import Transaction


class PurchaseBill(Base):
    __tablename__ = "purchase_bills"

    # --- 字段定义 (使用 Mapped 语法) ---
    guid: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    vendor_guid: Mapped[str] = mapped_column(ForeignKey("vendors.guid", ondelete="RESTRICT"), nullable=False)
    bill_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    bill_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    total_amount: Mapped[DECIMAL] = mapped_column(DECIMAL(15, 2), nullable=False, default=0.00)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    post_txn_guid: Mapped[str | None] = mapped_column(ForeignKey("transactions.guid", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(timezone.utc),
                                                 onupdate=datetime.now(timezone.utc))

    # --- 关系定义 ---
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="purchase_bills")

    # 正确的写法：使用 Mapped 语法，并且是单向关系
    posted_transaction: Mapped[Optional["Transaction"]] = relationship("Transaction")

