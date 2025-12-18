# app/schemas/reporting.py

from datetime import datetime, date

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from decimal import Decimal

class DashboardMetrics(BaseModel):
    """仪表盘核心指标"""
    total_assets: Decimal = Field(default=0.00, decimal_places=2, description="总资产")
    current_profit: Decimal = Field(default=0.00, decimal_places=2, description="本期利润")
    cash_balance: Decimal = Field(default=0.00, decimal_places=2, description="现金余额")
    total_revenue: Decimal = Field(default=0.00, decimal_places=2, description="营业收入")

    class Config:
        from_attributes = True

class CashFlowData(BaseModel):
    """现金流数据"""
    periods: List[str] = Field(default=[], description="期间列表")
    inflows: List[Decimal] = Field(default=[], description="流入金额列表")
    outflows: List[Decimal] = Field(default=[], description="流出金额列表")

    class Config:
        from_attributes = True

class ArApData(BaseModel):
    """应收应付数据"""
    receivables: List[Dict[str, Any]] = Field(default=[], description="应收账款列表")
    payables: List[Dict[str, Any]] = Field(default=[], description="应付账款列表")

    class Config:
        from_attributes = True

# --- 收支结构数据模型 ---
class IncomeExpenseData(BaseModel):
    """收支结构数据，用于饼图"""
    series: List[Dict[str, Any]] = Field(default=[], description="收支数据系列，例如 [{'name': '营业收入', 'value': 1000}]")

    class Config:
        from_attributes = True

class BalanceSheetRequest(BaseModel):
    """资产负债表请求"""
    period: str = Field(..., description="会计期间，如2023-10")

class BalanceSheetResponse(BaseModel):
    """资产负债表响应"""
    period: str = Field(..., description="会计期间")
    assets: Dict[str, Decimal] = Field(..., description="资产项目")
    liabilities: Dict[str, Decimal] = Field(..., description="负债项目")
    equity: Dict[str, Decimal] = Field(..., description="权益项目")
    total_assets: Decimal = Field(..., decimal_places=2, description="资产总计")
    total_liabilities: Decimal = Field(..., decimal_places=2, description="负债总计")
    total_equity: Decimal = Field(..., decimal_places=2, description="权益总计")

    class Config:
        from_attributes = True

class IncomeStatementRequest(BaseModel):
    """损益表请求"""
    period: str = Field(..., description="会计期间，如2023-10")
    comparison_period: Optional[str] = Field(None, description="对比期间，如2023-09")

class IncomeStatementResponse(BaseModel):
    """损益表响应"""
    period: str = Field(..., description="会计期间")
    comparison_period: Optional[str] = Field(None, description="对比期间")
    income_items: Dict[str, Decimal] = Field(..., description="收入项目")
    expense_items: Dict[str, Decimal] = Field(..., description="费用项目")
    total_income: Decimal = Field(..., decimal_places=2, description="收入总计")
    total_expense: Decimal = Field(..., decimal_places=2, description="费用总计")
    net_profit: Decimal = Field(..., decimal_places=2, description="净利润")
    comparison_net_profit: Optional[Decimal] = Field(None, decimal_places=2, description="对比期间净利润")

    class Config:
        from_attributes = True

class CashFlowStatementRequest(BaseModel):
    """现金流量表请求"""
    period: str = Field(..., description="会计期间，如2023-10")

class CashFlowStatementResponse(BaseModel):
    """现金流量表响应"""
    period: str = Field(..., description="会计期间")
    operating_activities: Dict[str, Decimal] = Field(..., description="经营活动现金流")
    investing_activities: Dict[str, Decimal] = Field(..., description="投资活动现金流")
    financing_activities: Dict[str, Decimal] = Field(..., description="筹资活动现金流")
    net_cash_flow: Decimal = Field(..., decimal_places=2, description="现金流量净额")

    class Config:
        from_attributes = True

class TrialBalanceRequest(BaseModel):
    """试算平衡表请求"""
    period: str = Field(..., description="会计期间，如2023-10")

class TrialBalanceResponse(BaseModel):
    """试算平衡表响应"""
    period: str = Field(..., description="会计期间")
    accounts: List[Dict[str, Any]] = Field(..., description="账户列表")
    total_debits: Decimal = Field(..., decimal_places=2, description="借方合计")
    total_credits: Decimal = Field(..., decimal_places=2, description="贷方合计")
    is_balanced: bool = Field(..., description="是否平衡")

    class Config:
        from_attributes = True

class ReportListResponse(BaseModel):
    """报表列表响应"""
    available_reports: List[str] = Field(..., description="可用报表类型")
    available_periods: List[str] = Field(..., description="可用期间列表")

    class Config:
        from_attributes = True

class ReportExportRequest(BaseModel):
    """报表导出请求"""
    report_type: str = Field(..., description="报表类型")
    period: str = Field(..., description="会计期间")
    format: str = Field(default="pdf", description="导出格式：pdf, excel, csv")

class ReportExportResponse(BaseModel):
    """报表导出响应"""
    download_url: str = Field(..., description="下载链接")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    expires_at: str = Field(..., description="链接过期时间")

    class Config:
        from_attributes = True

# --- 新增的自定义报表 Schemas ---

class CustomReportQuery(BaseModel):
    """自定义报表查询参数"""
    start_date: date = Field(..., description="报表开始日期")
    end_date: date = Field(..., description="报表结束日期")
    account_guids: Optional[List[str]] = Field(None, description="指定查询的账户GUID列表，为空则查询所有")

class CustomReportLine(BaseModel):
    """自定义报表行数据"""
    account_guid: str
    account_code: Optional[str]
    account_name: str
    account_type: str
    beginning_balance: float = Field(..., description="期初余额")
    debit_total: float = Field(..., description="借方发生额合计")
    credit_total: float = Field(..., description="贷方发生额合计")
    ending_balance: float = Field(..., description="期末余额")

class CustomReportResponse(BaseModel):
    """自定义报表响应"""
    query: CustomReportQuery
    generated_at: datetime
    lines: List[CustomReportLine]
    total_debit: float
    total_credit: float

# --- 年月列表模型 ---
class PeriodList(BaseModel):
    """API响应模型：年月列表"""
    periods: list[str]


__all__ = [
    "DashboardMetrics",
    "CashFlowData",
    "ArApData",
    "IncomeExpenseData",
    "BalanceSheetRequest",
    "BalanceSheetResponse",
    "IncomeStatementRequest",
    "IncomeStatementResponse",
    "CashFlowStatementRequest",
    "CashFlowStatementResponse",
    "TrialBalanceRequest",
    "TrialBalanceResponse",
    "ReportListResponse",
    "ReportExportRequest",
    "ReportExportResponse",
    "CustomReportResponse",
    "CustomReportLine",
    "CustomReportQuery",
    "PeriodList"
]
