# app/api/v1/endpoints/employee_expense.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import deps
from app.schemas.user import UserWithAuth

from app.schemas import employee as employee_schemas
from app.schemas import expense as expense_schemas

from app.crud import crud_employee
from app.crud import crud_expense

router = APIRouter()


# --- 员工管理 API ---

@router.get("/employees", response_model=list[employee_schemas.Employee])
async def read_employees(
        db: AsyncSession = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
):
    """获取员工列表"""
    return await crud_employee.get_multi(db, skip=skip, limit=limit)


@router.post("/employees", response_model=employee_schemas.Employee, status_code=status.HTTP_201_CREATED)
async def create_employee(
        *,
        db: AsyncSession = Depends(deps.get_db),
        employee_in: employee_schemas.EmployeeCreate,
        current_user: UserWithAuth = Depends(deps.get_current_active_superuser),
):
    """创建新员工 (仅超级用户)"""
    user = await crud_employee.get_by_username(db, username=employee_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="该用户名已存在",
        )
    return await crud_employee.create(db=db, obj_in=employee_in)


@router.put("/employees/{guid}", response_model=employee_schemas.Employee)
async def update_employee(
        guid: str,
        *,
        db: AsyncSession = Depends(deps.get_db),
        employee_in: employee_schemas.EmployeeUpdate,
        current_user: UserWithAuth = Depends(deps.get_current_active_user)
):
    """更新员工信息"""
    db_employee = await crud_employee.get(db=db, id=guid)
    if not db_employee:
        raise HTTPException(status_code=404, detail="员工未找到")
    return await crud_employee.update(db=db, db_obj=db_employee, obj_in=employee_in)


@router.get("/employees/{guid}", response_model=employee_schemas.Employee)
async def read_employee(
        guid: str,
        db: AsyncSession = Depends(deps.get_db),
):
    """通过 GUID 获取单个员工信息"""
    db_employee = await crud_employee.get(db=db, id=guid)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="员工未找到")
    return db_employee


@router.delete("/employees/{guid}", response_model=employee_schemas.Employee)
async def delete_employee(
        guid: str,
        db: AsyncSession = Depends(deps.get_db),
        current_user: UserWithAuth = Depends(deps.get_current_active_superuser),
):
    """删除员工 (仅超级用户)"""
    db_employee = await crud_employee.get(db=db, id=guid)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="员工未找到")
    return await crud_employee.remove(db=db, id=guid)

# --- 费用报销 API ---

@router.get("/reports", response_model=list[expense_schemas.ExpenseReport])
async def read_expense_reports(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: UserWithAuth = Depends(deps.get_current_active_user),
):
    """
    获取费用报告列表。
    - 超级用户可以看到所有报告。
    - 普通用户只能看到自己的报告。
    """
    return await crud_expense.get_multi_expense_reports(
        db=db, skip=skip, limit=limit, current_user=current_user
    )


@router.get("/my-reports", response_model=list[expense_schemas.ExpenseReport])
async def read_my_expense_reports(
        db: AsyncSession = Depends(deps.get_db),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1),
        current_user: UserWithAuth = Depends(deps.get_current_active_user),
):
    """获取当前用户的费用报告"""
    return await crud_expense.get_multi_expense_reports(
        db=db, employee_guid=current_user.guid, skip=skip, limit=limit
    )


@router.post("/reports", response_model=expense_schemas.ExpenseReport, status_code=status.HTTP_201_CREATED)
async def create_expense_report(
        *,
        db: AsyncSession = Depends(deps.get_db),
        report_in: expense_schemas.ExpenseReportCreate,
        current_user: UserWithAuth = Depends(deps.get_current_active_user),
):
    """提交新的费用报告"""
    return await crud_expense.create_expense_report(db=db, obj_in=report_in, current_user=current_user)


@router.patch("/reports/{guid}/approve", response_model=expense_schemas.ExpenseReport)
async def approve_expense_report(
        guid: str,
        *,
        db: AsyncSession = Depends(deps.get_db),
        approval_in: expense_schemas.ExpenseReportApproval,
        current_user: UserWithAuth = Depends(deps.get_current_active_superuser),
):
    """审批费用报告 (仅超级用户)"""
    report = await crud_expense.approve_expense_report(db=db, guid=guid, obj_in=approval_in,
                                                       reviewer_guid=current_user.guid)
    if not report:
        raise HTTPException(status_code=404, detail="费用报告未找到或状态不允许审批")
    return report


@router.get("/reports/{guid}", response_model=expense_schemas.ExpenseReport)
async def read_expense_report(
        guid: str,
        db: AsyncSession = Depends(deps.get_db),
        current_user: UserWithAuth = Depends(deps.get_current_active_user),
):
    """通过 GUID 获取单个费用报告"""
    report = await crud_expense.get_expense_report(db, guid=guid)
    if not report:
        raise HTTPException(status_code=404, detail="费用报告未找到")
    if report.get("employee_guid") != current_user.guid and current_user.acl != "admin":
        raise HTTPException(status_code=403, detail="没有权限查看此报告")

    return report


@router.delete("/reports/{guid}", response_model=expense_schemas.ExpenseReport)
async def delete_expense_report(
        guid: str,
        db: AsyncSession = Depends(deps.get_db),
        current_user: UserWithAuth = Depends(deps.get_current_active_user),
):
    """删除费用报告 (仅提交者或超级用户)"""
    report = await crud_expense.delete_expense_report(db, guid=guid)
    if not report:
        raise HTTPException(status_code=404, detail="费用报告未找到或无法删除")
    return report
