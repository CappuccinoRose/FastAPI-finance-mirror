# app/schemas/vendor.py
import uuid
from pydantic import BaseModel, Field

class VendorBase(BaseModel):
    name: str = Field(..., max_length=255)
    id: str | None = Field(None, max_length=50)
    notes: str | None = None
    active: bool = True

class VendorCreate(VendorBase):
    guid: uuid.UUID = Field(default_factory=uuid.uuid4)

class VendorUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    id: str | None = Field(None, max_length=50)
    notes: str | None = None
    active: bool | None = None

# Vendor 和 VendorBase 保持不变
class Vendor(VendorBase):
    guid: str

    class Config:
        from_attributes = True
