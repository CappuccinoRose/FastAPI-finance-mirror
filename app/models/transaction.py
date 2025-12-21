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
    # 同样，这里也加入 PurchaseBill 的类型提示，以保持对称性
    from app.models.purchase_bill import PurchaseBill


class Transaction(Base):
    __tablename__ = "transactions"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=uuid4)
    post_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    enter_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT)

    # --- 关系定义 ---

    # 1. 与 Split 的关系 (一对多)
    splits: Mapped[list["Split"]] = relationship("Split", back_populates="transaction", cascade="all, delete-orphan",
                                                 passive_deletes=True)

    # 2. 与 Invoice 的反向关系 (一对一)
    # 这个关系与 Invoice.post_transaction 配对
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="post_transaction", uselist=False)

    # 3. (可选) 与 PurchaseBill 的反向关系
    # 如果你需要从 Transaction 对象访问其对应的 PurchaseBill，可以取消下面这行的注释
    # source_purchase_bill: Mapped[Optional["PurchaseBill"]] = relationship("PurchaseBill", back_populates="posted_transaction")
