from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- 直接导入所有相关的 Schema ---
from app.schemas.customer import Customer as CustomerSchema
from app.schemas.account import Account as AccountSchema

# --- Entry Schemas (发票条目) ---
class EntryBase(BaseModel):
    date: datetime
    description: str
    action: Optional[str] = None
    account_guid: str
    quantity_num: int = 1
    quantity_denom: int = 1
    price: float
    discounted: bool = False

class EntryCreate(EntryBase):
    """创建发票条目时使用，不需要 invoice_guid"""
    pass

class Entry(EntryBase):
    """用于 API 返回的发票条目模型"""
    guid: str
    invoice_guid: str
    account: Optional[AccountSchema] = None

    class Config:
        from_attributes = True

# --- Invoice Schemas (发票) ---
class InvoiceBase(BaseModel):
    id: str = Field(..., max_length=50)
    owner_guid: str
    customer_guid: Optional[str] = None
    date_posted: Optional[datetime] = None
    date_due: Optional[datetime] = None
    notes: Optional[str] = None
    active: bool = True

class InvoiceCreate(InvoiceBase):
    """创建发票时使用，包含一个条目列表"""
    entries: List[EntryCreate] = Field(min_items=1)

class InvoiceUpdate(BaseModel):
    """更新发票时使用，所有字段可选，不包含条目"""
    id: Optional[str] = Field(None, max_length=50)
    owner_guid: Optional[str] = None
    customer_guid: Optional[str] = None
    date_posted: Optional[datetime] = None
    date_due: Optional[datetime] = None
    notes: Optional[str] = None
    active: Optional[bool] = None

class Invoice(InvoiceBase):
    """用于 API 返回的完整发票模型，包含条目和关联客户"""
    guid: str
    post_txn: Optional[str] = None
    customer: Optional[CustomerSchema] = None
    # 关联的条目列表
    entries: List[Entry] = []

    class Config:
        from_attributes = True

# --- 在所有模型定义后，重建它们以解决循环引用 ---
# 这是解决循环导入问题的核心步骤
Entry.model_rebuild()
Invoice.model_rebuild()
