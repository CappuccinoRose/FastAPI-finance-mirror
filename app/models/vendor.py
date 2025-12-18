# app/models/vendor.py
from sqlalchemy import String, TEXT, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# 为了避免循环导入，使用 TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.purchase_bill import PurchaseBill

class Vendor(Base):
    __tablename__ = "vendors"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    id: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(TEXT)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('TRUE'))
    purchase_bills: Mapped[list["PurchaseBill"]] = relationship(
        "PurchaseBill", back_populates="vendor"
    )
