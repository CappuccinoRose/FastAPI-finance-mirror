from decimal import Decimal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.schemas.account import Account

class SplitBase(BaseModel):
    memo: Optional[str] = Field(None, max_length=255)
    action: Optional[str] = Field(None, max_length=50)
    quantity_num: int = 0
    quantity_denom: int = 1
    value: Decimal = Field(default=0.00, decimal_places=2)
    reconcile_state: str = Field(default='n', max_length=1)
    reconcile_date: Optional[datetime] = None

    @validator('quantity_denom')
    def denominator_must_not_be_zero(cls, v):
        if v == 0:
            raise ValueError('分母 (quantity_denom) 不能为零')
        return v

class SplitCreate(SplitBase):
    txn_guid: str
    account_guid: str

class SplitUpdate(BaseModel):
    memo: Optional[str] = Field(None, max_length=255)
    action: Optional[str] = Field(None, max_length=50)
    quantity_num: Optional[int] = None
    quantity_denom: Optional[int] = None
    value: Optional[Decimal] = Field(None, decimal_places=2)
    reconcile_state: Optional[str] = Field(None, max_length=1)
    reconcile_date: Optional[datetime] = None

class Split(SplitBase):
    guid: str
    txn_guid: str
    account_guid: str

    class Config:
        from_attributes = True
