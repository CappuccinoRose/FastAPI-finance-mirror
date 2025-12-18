# app/schemas/customer.py
from pydantic import BaseModel, Field
from typing import List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免循环依赖
    from .invoice import Invoice

class CustomerBase(BaseModel):
    name: str = Field(..., max_length=255)
    id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    active: bool = True

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    active: Optional[bool] = None

class Customer(CustomerBase):
    guid: str

    class Config:
        from_attributes = True

