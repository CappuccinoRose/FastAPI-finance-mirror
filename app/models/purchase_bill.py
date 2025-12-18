import uuid

from sqlalchemy import Column, String, Date, Text, DECIMAL, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from .base import BaseModel


class PurchaseBill(BaseModel):
    __tablename__ = "purchase_bills"

    guid = Column(CHAR(36), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    vendor_guid = Column(String(36), ForeignKey("vendors.guid", ondelete="RESTRICT"), nullable=False)
    bill_number = Column(String(50), nullable=False, unique=True, index=True)
    bill_date = Column(Date, nullable=False)
    due_date = Column(Date)
    total_amount = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    notes = Column(Text)
    status = Column(String(20), nullable=False, default="draft", index=True) # draft, confirmed, posted, cancelled
    post_txn_guid = Column(String(36), ForeignKey("transactions.guid", ondelete="SET NULL"))

    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_bills")
    # 使用 backref 在 Transaction 模型上动态创建一个反向引用
    posted_transaction = relationship("Transaction", backref="purchase_bill")