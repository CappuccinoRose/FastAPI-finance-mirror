# app/schemas/expense.py
from typing import Optional, List
from pydantic import BaseModel

class ExpenseEntryBase(BaseModel):
    category: str
    description: str
    amount: float

class ExpenseEntryCreate(ExpenseEntryBase):
    # 前端创建时不包含 receipt_url
    pass

class ExpenseEntry(ExpenseEntryBase):
    # 从数据库读取时可能包含 receipt_url
    receipt_url: Optional[str] = None

    class Config:
        from_attributes = True

class ExpenseReportBase(BaseModel):
    description: str

class ExpenseReportCreate(ExpenseReportBase):
    entries: List[ExpenseEntryCreate]

class ExpenseReportApproval(BaseModel):
    status: str # 'APPROVED' or 'REJECTED'
    notes: Optional[str] = None

class ExpenseReport(ExpenseReportBase):
    guid: str
    total_amount: float
    employee_guid: str
    status: str
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewer_guid: Optional[str] = None
    notes: Optional[str] = None
    entries: List[ExpenseEntry] = []

    class Config:
        from_attributes = True

# 这个 Schema 在当前逻辑下暂时用不到，但保留以备将来扩展
class ExpenseReportUpdate(BaseModel):
    description: Optional[str] = None
    notes: Optional[str] = None
