# app/models/transaction.py

from uuid import uuid4
from sqlalchemy import String, TEXT, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base

# 为了避免循环导入，使用 TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.split import Split
    from app.models.invoice import Invoice
    # 注意：我们不再需要从 PurchaseBill 导入，因为 Transaction 不再直接定义与它的关系

class Transaction(Base):
    __tablename__ = "transactions"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=uuid4)
    post_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    enter_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT)

    # --- 关系定义 ---

    # 1. 与 Split 的关系 (一对多)
    splits: Mapped[list["Split"]] = relationship("Split", back_populates="transaction", cascade="all, delete-orphan", passive_deletes=True)

    # 2. 与 Invoice 的反向关系 (一对一)
    # 这个关系与 Invoice.post_transaction 配对
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="post_transaction", uselist=False)

    # --- 删除的内容 ---
    # 彻底删除 source_purchase_bill 关系，它是不需要的，并且是冲突的根源。
    # source_purchase_bill: Mapped["PurchaseBill"] = relationship(...)
    #
    # 删除 invoices 关系，因为它与上面的 invoice 命名冲突且不清晰。
    # invoices: Mapped[list["Invoice"]] = relationship(...)

