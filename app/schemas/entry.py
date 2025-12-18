from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .invoice import Invoice
    from .account import Account

class EntryBase(BaseModel):
    date: datetime
    description: str
    action: Optional[str] = Field(None, max_length=50)
    account_guid: str
    quantity_num: int = 0
    quantity_denom: int = 1
    price: Decimal = Field(default=0.00, decimal_places=2)
    discounted: bool = False

class EntryCreate(EntryBase):
    invoice_guid: str

class EntryUpdate(BaseModel):
    date: Optional[datetime] = None
    description: Optional[str] = None
    action: Optional[str] = Field(None, max_length=50)
    account_guid: Optional[str] = None
    quantity_num: Optional[int] = None
    quantity_denom: Optional[int] = None
    price: Optional[Decimal] = Field(None, decimal_places=2)
    discounted: Optional[bool] = None

class Entry(EntryBase):
    guid: str
    invoice_guid: str
    invoice: "Invoice"
    account: "Account"

    class Config:
        from_attributes = True
