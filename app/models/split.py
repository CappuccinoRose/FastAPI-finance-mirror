# app/models/split.py
from uuid import uuid4
from sqlalchemy import String, Numeric, ForeignKey, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING

from app.db.base import Base

# 将跨模型导入移入 TYPE_CHECKING 块
if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.account import Account

class Split(Base):
    __tablename__ = "splits"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=uuid4)
    txn_guid: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.guid", ondelete="CASCADE"), nullable=False, index=True)
    account_guid: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.guid", ondelete="RESTRICT"), nullable=False, index=True)
    memo: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str | None] = mapped_column(String(50))
    reconcile_state: Mapped[str] = mapped_column(String(1), nullable=False, server_default='n')
    reconcile_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0.00)
    quantity_num: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_denom: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # 关系定义保持不变，使用字符串引用
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="splits")
    account: Mapped["Account"] = relationship("Account", back_populates="splits")
