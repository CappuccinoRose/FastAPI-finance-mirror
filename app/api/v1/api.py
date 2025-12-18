# finance_mirror_backend/app/api/v1/api.py
# 完成路由配置，与前端配合
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    general_ledger,
    accounts_receivable,
    accounts_payable,
    employee_expense,
    reporting,
    system_config,
    period_closing,
    document_posting
)

api_router = APIRouter()

# 包含认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 包含业务领域路由
api_router.include_router(general_ledger.router, prefix="/accounts", tags=["总账管理"])
api_router.include_router(accounts_receivable.router, prefix="/receivable", tags=["应收账款"])
api_router.include_router(accounts_payable.router, prefix="/payable", tags=["应付账款"])
api_router.include_router(employee_expense.router, prefix="/expenses", tags=["员工费用"])
api_router.include_router(reporting.router, prefix="/reports", tags=["财务报表"])
api_router.include_router(system_config.router, prefix="/system", tags=["系统配置"])
api_router.include_router(period_closing.router, prefix="/period-closings", tags=["报表与结账"])
api_router.include_router(document_posting.router, prefix="/document-posting", tags=["单据过账"])

