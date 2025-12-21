# app/models/customer.py
from sqlalchemy import String, TEXT, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4
from typing import TYPE_CHECKING

from app.db.base import Base

# 将跨模型导入移入 TYPE_CHECKING 块
if TYPE_CHECKING:
    from app.models.invoice import Invoice

class Customer(Base):
    __tablename__ = "customers"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    id: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(TEXT)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 关系定义保持不变，使用字符串引用
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="customer")
