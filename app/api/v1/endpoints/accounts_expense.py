# app/api/v1/endpoints/employee_expense.py
# 会计管理部分内容
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, crud
from app.api.v1 import deps

router = APIRouter()

# --- Employees ---
@router.post("/employees", response_model=schemas.Employee)
async def create_employee(
    *,
    db: AsyncSession = Depends(deps.get_db),
    employee_in: schemas.EmployeeCreate,
) -> Any:
    """
    Create new employee.
    """
    # TODO: Implement CRUD logic
    raise HTTPException(status_code=501, detail="Not Implemented")

# --- Expense Reports ---
@router.post("/expense-reports", response_model=schemas.ExpenseReport)
async def create_expense_report(
    *,
    db: AsyncSession = Depends(deps.get_db),
    report_in: schemas.ExpenseReportCreate,
) -> Any:
    """
    Create new expense report.
    """
    # TODO: Implement CRUD logic
    raise HTTPException(status_code=501, detail="Not Implemented")
