# finance_mirror_backend/app/schemas/__init__.py

# 导入所有模型以确保它们被注册
from .account import Account, AccountBase, AccountCreate, AccountUpdate
from .document_posting import DocumentPostingCreate, DocumentPostingResponse, DocumentType
from .transaction import Transaction, TransactionBase, TransactionCreate, TransactionUpdate
from .split import Split, SplitBase, SplitCreate, SplitUpdate
from .customer import Customer, CustomerBase, CustomerCreate, CustomerUpdate
from .vendor import Vendor, VendorBase, VendorCreate, VendorUpdate
from .employee import Employee, EmployeeBase, EmployeeCreate, EmployeeUpdate
from .invoice import Invoice, InvoiceBase, InvoiceCreate, InvoiceUpdate, Entry, EntryCreate
from .entry import Entry as DBEntry, EntryBase as DBEntryBase, EntryCreate as DBEntryCreate, \
    EntryUpdate as DBEntryUpdate, EntryBase, EntryUpdate
from .slot import Slot, SlotBase, SlotCreate, SlotUpdate
from .user import Token, TokenData, User, UserCreate, UserWithAuth
from .auth import PasswordResetRequest, PasswordResetResponse, PasswordResetConfirm
from .purchase_bill import (
    PurchaseBill,
    PurchaseBillBase,
    PurchaseBillCreate,
    PurchaseBillUpdate,
    PurchaseBillSummary,
)

# 为了方便外部导入，可以在这里重新导出
__all__ = [
    "Account", "AccountBase", "AccountCreate", "AccountUpdate",
    "DocumentPostingCreate", "DocumentPostingResponse", "DocumentType",
    "Transaction", "TransactionBase", "TransactionCreate", "TransactionUpdate",
    "Split", "SplitBase", "SplitCreate", "SplitUpdate",
    "Customer", "CustomerBase", "CustomerCreate", "CustomerUpdate",
    "Vendor", "VendorBase", "VendorCreate", "VendorUpdate",
    "Employee", "EmployeeBase", "EmployeeCreate", "EmployeeUpdate",
    "Invoice", "InvoiceBase", "InvoiceCreate", "InvoiceUpdate", "Entry", "EntryCreate",
    "Entry", "EntryBase", "EntryCreate", "EntryUpdate",
    "Slot", "SlotBase", "SlotCreate", "SlotUpdate",
    "Token", "TokenData", "User", "UserCreate", "UserWithAuth",
    "PasswordResetRequest", "PasswordResetResponse", "PasswordResetConfirm",
    "PurchaseBill",
    "PurchaseBillBase",
    "PurchaseBillCreate",
    "PurchaseBillUpdate",
    "PurchaseBillSummary",
]


def rebuild_models():
    """重建所有具有前向引用的 Pydantic 模型"""
    # 导入所有需要重建的模型
    from .invoice import Invoice, Entry
    from .customer import Customer
    from .account import Account
    from .purchase_bill import PurchaseBill, PurchaseBillSummary
    from .vendor import Vendor

    namespace = {
        "Customer": Customer,
        "Account": Account,
        "Invoice": Invoice,
        "Entry": Entry,
        "PurchaseBill": PurchaseBill,
        "PurchaseBillSummary": PurchaseBillSummary,
        "Vendor": Vendor,
    }

    Invoice.model_rebuild(_types_namespace=namespace)
    Entry.model_rebuild(_types_namespace=namespace)
    Customer.model_rebuild(_types_namespace=namespace)
    Account.model_rebuild(_types_namespace=namespace)
    PurchaseBill.model_rebuild(_types_namespace=namespace)
    PurchaseBillSummary.model_rebuild(_types_namespace=namespace)
    Vendor.model_rebuild(_types_namespace=namespace)


# 执行重建
rebuild_models()
