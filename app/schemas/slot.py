from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class SlotBase(BaseModel):
    obj_guid: str
    name: str = Field(..., max_length=255)
    slot_type: str = Field(..., max_length=50)

class SlotCreate(SlotBase):
    string_val: Optional[str] = None
    numeric_val: Optional[Decimal] = Field(None, decimal_places=2)

class SlotUpdate(BaseModel):
    string_val: Optional[str] = None
    numeric_val: Optional[Decimal] = Field(None, decimal_places=2)

class Slot(SlotBase):
    string_val: Optional[str] = None
    numeric_val: Optional[Decimal] = Field(None, decimal_places=2)

    class Config:
        from_attributes = True
