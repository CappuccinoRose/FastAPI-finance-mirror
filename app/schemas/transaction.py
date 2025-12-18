from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import TYPE_CHECKING
from .split import Split, SplitCreate

if TYPE_CHECKING:
    from app.schemas.split import SplitCreate, Split

class TransactionBase(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    post_date: datetime
    enter_date: datetime

class TransactionCreate(TransactionBase):
    splits: List[SplitCreate] = []

    @validator('splits')
    def splits_must_balance(cls, v):
        total_value = sum(split.value for split in v)
        if total_value != 0:
            raise ValueError('所有分录的金额总和必须为零（借贷平衡）')
        return v

class TransactionUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    post_date: Optional[datetime] = None
    enter_date: Optional[datetime] = None

class Transaction(TransactionBase):
    guid: str
    splits: List[Split] = []

    class Config:
        from_attributes = True
