from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

class PurchaseBillBase(BaseModel):
    vendor_guid: str = Field(..., description="供应商GUID")
    bill_number: str = Field(..., description="账单号")
    bill_date: date = Field(..., description="账单日期")
    due_date: Optional[date] = Field(None, description="到期日")
    total_amount: Decimal = Field(Decimal('0.00'), description="总金额")
    notes: Optional[str] = Field(None, description="备注")
    status: str = Field("draft", description="状态")

class PurchaseBillCreate(PurchaseBillBase):
    pass

class PurchaseBillUpdate(BaseModel):
    vendor_guid: Optional[str] = None
    bill_number: Optional[str] = None
    bill_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    post_txn_guid: Optional[str] = None

class PurchaseBill(PurchaseBillBase):
    model_config = ConfigDict(from_attributes=True)

    guid: str
    post_txn_guid: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class PurchaseBillSummary(PurchaseBill):
    vendor: Optional['Vendor'] = None
