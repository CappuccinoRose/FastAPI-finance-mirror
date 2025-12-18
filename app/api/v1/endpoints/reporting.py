# finance_mirror_backend/app/api/v1/endpoints/reporting.py

from typing import Any, List

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import deps
from app.core.exceptions import BusinessException
from app.crud import crud_reporting
from app.schemas import reporting as reporting_schemas
from app.schemas.account import Account as AccountSchema
from app.schemas.user import User
from app.models.account import Account

router = APIRouter()


@router.get("/dashboard/metrics", response_model=reporting_schemas.DashboardMetrics, summary="获取仪表盘核心指标")
async def get_dashboard_metrics(
        period: str | None = Query(None,
                                   description="可选的会计期间，格式为 YYYY-MM，如 2024-01。不填则返回当前最新数据。"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        metrics = await crud_reporting.get_dashboard_metrics(db, period)
        return metrics
    except Exception as e:
        raise BusinessException(detail=f"获取仪表盘指标失败: {str(e)}")


# --- 以下路由保持不变 ---
@router.get("/dashboard/cash-flow", response_model=reporting_schemas.CashFlowData, summary="获取现金流概览")
async def get_cash_flow_overview(
        period: str = Query(..., description="会计期间，如2023-10"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        cash_flow_data = await crud_reporting.get_cash_flow_data(db, period)
        return cash_flow_data
    except Exception as e:
        raise BusinessException(detail=f"获取现金流数据失败: {str(e)}")


@router.get("/dashboard/ar-ap", response_model=reporting_schemas.ArApData, summary="获取应收应付概况")
async def get_ar_ap_overview(
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        ar_ap_data = await crud_reporting.get_ar_ap_data(db)
        return ar_ap_data
    except Exception as e:
        raise BusinessException(detail=f"获取应收应付数据失败: {str(e)}")


@router.get("/dashboard/income-expense", response_model=reporting_schemas.IncomeExpenseData, summary="获取收支结构数据")
async def get_income_expense_data(
        period: str = Query(..., description="会计期间，如2023-10"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        income_expense_data = await crud_reporting.get_income_expense_data(db, period)
        return income_expense_data
    except Exception as e:
        raise BusinessException(detail=f"获取收支结构数据失败: {str(e)}")


@router.get("/periods", response_model=reporting_schemas.PeriodList, summary="获取所有可查询的年月列表")
async def get_available_periods(
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        periods = await crud_reporting.get_available_periods(db=db)
        return reporting_schemas.PeriodList(periods=periods)
    except Exception as e:
        raise BusinessException(detail=f"获取可用年月失败: {str(e)}")


# --- Standard Report Generation Endpoints (已实现) ---

@router.post("/balance-sheet", response_model=reporting_schemas.BalanceSheetResponse,
             summary="生成资产负债表", status_code=status.HTTP_201_CREATED)
async def generate_balance_sheet(
        report_request: reporting_schemas.BalanceSheetRequest,
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        report_data = await crud_reporting.generate_balance_sheet(db, report_request.period)
        return report_data
    except Exception as e:
        if "no data" in str(e).lower() or "无数据" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="所选会计期间内无任何业务数据，无法生成报表")
        raise BusinessException(detail=f"生成资产负债表失败: {str(e)}")


@router.post("/income-statement", response_model=reporting_schemas.IncomeStatementResponse,
             summary="生成损益表", status_code=status.HTTP_201_CREATED)
async def generate_income_statement(
        report_request: reporting_schemas.IncomeStatementRequest,
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        report_data = await crud_reporting.generate_income_statement(db, report_request.period,
                                                                     report_request.comparison_period)
        return report_data
    except Exception as e:
        if "no data" in str(e).lower() or "无数据" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="所选会计期间内无任何业务数据，无法生成报表")
        raise BusinessException(detail=f"生成损益表失败: {str(e)}")


@router.post("/cash-flow-statement", response_model=reporting_schemas.CashFlowStatementResponse,
             summary="生成现金流量表", status_code=status.HTTP_201_CREATED)
async def generate_cash_flow_statement(
        report_request: reporting_schemas.CashFlowStatementRequest,
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        report_data = await crud_reporting.generate_cash_flow_statement(db, report_request.period)
        return report_data
    except Exception as e:
        if "no data" in str(e).lower() or "无数据" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="所选会计期间内无任何业务数据，无法生成报表")
        raise BusinessException(detail=f"生成现金流量表失败: {str(e)}")


@router.post("/trial-balance", response_model=reporting_schemas.TrialBalanceResponse,
             summary="生成试算平衡表", status_code=status.HTTP_201_CREATED)
async def generate_trial_balance(
        report_request: reporting_schemas.TrialBalanceRequest,
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        report_data = await crud_reporting.generate_trial_balance(db, report_request.period)
        return report_data
    except Exception as e:
        if "no data" in str(e).lower() or "无数据" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="所选会计期间内无任何业务数据，无法生成报表")
        raise BusinessException(detail=f"生成试算平衡表失败: {str(e)}")


@router.get("/accounts", response_model=List[AccountSchema], summary="获取所有账户列表")
async def get_all_accounts(
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        result = await db.execute(select(Account))
        accounts = result.scalars().all()
        return accounts
    except Exception as e:
        raise BusinessException(detail=f"获取账户列表失败: {str(e)}")


@router.post("/custom", response_model=reporting_schemas.CustomReportResponse, summary="生成自定义实时报表")
async def generate_custom_report(
        query: reporting_schemas.CustomReportQuery,
        db: AsyncSession = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    try:
        report_data = await crud_reporting.get_custom_report_data(db, query)
        return report_data
    except Exception as e:
        raise BusinessException(detail=f"生成自定义报表失败: {str(e)}")

