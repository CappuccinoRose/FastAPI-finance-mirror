# app/crud/crud_expense.py
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# 导入我们实际拥有的模型
from app.models.purchase_bill import PurchaseBill
from app.models.employee import Employee
from app.models.transaction import Transaction
from app.models.split import Split

from app.schemas.user import UserWithAuth
from app.schemas import expense as expense_schemas

SYSTEM_EMPLOYEE_USERNAME = "system.expense"

# 【注意】这是一个内存中的模拟数据库，仅用于演示。
# 在生产环境中，这应该被替换为真实的数据库表和模型。
MOCK_EXPENSE_REPORT_DB: List[Dict[str, Any]] = [
    {
        "guid": "mock-expense-001-guid",
        "description": "【模拟】张伟的差旅报销",
        "total_amount": 3500.50,
        "employee_guid": "emp-finance-001-guid",
        "status": "SUBMITTED",
        "submitted_at": "2024-05-15T10:00:00Z",
        "entries": [
            {"category": "交通费", "description": "往返机票", "amount": 2500.00},
            {"category": "住宿费", "description": "酒店住宿2晚", "amount": 800.00},
            {"category": "餐补", "description": "3天伙食补贴", "amount": 200.50}
        ]
    },
    {
        "guid": "mock-expense-002-guid",
        "description": "【模拟】李娜的办公用品采购",
        "total_amount": 1200.00,
        "employee_guid": "emp-finance-002-guid",
        "status": "APPROVED",
        "submitted_at": "2024-05-10T14:30:00Z",
        "reviewed_at": "2024-05-11T09:00:00Z",
        "reviewer_guid": "emp-admin-guid",
        "entries": [
            {"category": "办公用品费", "description": "购买打印纸和墨盒", "amount": 1200.00}
        ]
    }
]


class CRUDExpense:
    """
    费用报告的 CRUD 操作。
    【新逻辑】此模块支持两种模式：
    1. 模拟模式：从 purchase_bills 表中读取并转换数据。
    2. 真实模式：操作一个模拟的、独立的费用报告数据源。
    """

    async def get_multi_expense_reports(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100, current_user: UserWithAuth,
            employee_guid: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取费用报告列表。
        - 如果提供了 employee_guid，则从模拟的真实报告中查询。
        - 如果没有提供 employee_guid，则从 purchase_bills 中模拟数据（用于管理员查看所有费用）。
        """
        if employee_guid:
            logger.info(f"查询用户 {employee_guid} 的真实费用报告。")
            reports = [r for r in MOCK_EXPENSE_REPORT_DB if r["employee_guid"] == employee_guid]
        else:
            logger.info(f"用户 {current_user.username} (权限: {current_user.acl}) 请求从采购账单生成的费用报告列表。")
            if "admin" not in current_user.acl:
                logger.warning(f"用户 {current_user.username} 无权查看从采购账单生成的费用报告。")
                return []

            try:
                query = (
                    select(PurchaseBill)
                    .options(
                        selectinload(PurchaseBill.vendor),
                        selectinload(PurchaseBill.posted_transaction)
                        .selectinload(Transaction.splits)
                        .selectinload(Split.account)
                    )
                    .where(PurchaseBill.status == 'posted')
                    .order_by(PurchaseBill.bill_date.desc())
                )

                result = await db.execute(query)
                posted_bills = result.scalars().unique().all()

                system_employee = await self._get_or_create_system_employee(db)
                if not system_employee:
                    logger.error("无法获取或创建系统员工，无法生成费用报告。")
                    return []

                reports = []
                for bill in posted_bills:
                    entries = []
                    if bill.posted_transaction:
                        for split in bill.posted_transaction.splits:
                            # 只关心贷方（负值）的分录，通常是费用类科目
                            if split.value < 0 and split.account:
                                entries.append({
                                    "category": split.account.name,
                                    "description": split.memo or bill.notes,
                                    "amount": float(abs(split.value))
                                })
                    if not entries:
                        continue

                    report_obj = {
                        "guid": bill.guid,
                        "description": f"{bill.vendor.name if bill.vendor else '未知供应商'} - {bill.notes}",
                        "total_amount": float(bill.total_amount),
                        "employee_guid": system_employee.guid,
                        "status": "APPROVED",
                        "submitted_at": bill.bill_date.isoformat() if bill.bill_date else None,
                        "entries": entries
                    }
                    reports.append(report_obj)

            except SQLAlchemyError as e:
                logger.error(f"从采购账单查询费用报告时发生数据库错误: {e}")
                return []

        # 分页
        paginated_reports = reports[skip: skip + limit]
        logger.info(f"最终返回 {len(paginated_reports)} 个有效的费用报告。")
        return paginated_reports

    async def get_expense_report(self, db: AsyncSession, *, guid: str) -> Optional[Dict[str, Any]]:
        """【真实模式】根据 GUID 获取单个费用报告"""
        # 【注意】此操作不涉及数据库，因此无需添加数据库异常处理
        for report in MOCK_EXPENSE_REPORT_DB:
            if report["guid"] == guid:
                return report
        return None

    async def create_expense_report(
            self, db: AsyncSession, *, obj_in: expense_schemas.ExpenseReportCreate, current_user: UserWithAuth
    ) -> Dict[str, Any]:
        """【真实模式】创建新的费用报告"""
        # 【注意】此操作不涉及数据库，因此无需添加数据库异常处理
        new_report = {
            "guid": f"mock-expense-{uuid.uuid4().hex[:8]}-guid",
            "description": obj_in.description,
            "total_amount": sum(entry.amount for entry in obj_in.entries),
            "employee_guid": current_user.guid,
            "status": "SUBMITTED",
            "submitted_at": datetime.utcnow().isoformat() + "Z",
            "entries": [entry.model_dump() for entry in obj_in.entries] # 使用 model_dump()
        }
        MOCK_EXPENSE_REPORT_DB.append(new_report)
        logger.info(f"用户 {current_user.username} 创建了新的费用报告: {new_report['guid']}")
        return new_report

    async def approve_expense_report(
            self, db: AsyncSession, *, guid: str, obj_in: expense_schemas.ExpenseReportApproval, reviewer_guid: str
    ) -> Optional[Dict[str, Any]]:
        """【真实模式】审批费用报告"""
        # 【注意】此操作不涉及数据库，因此无需添加数据库异常处理
        for report in MOCK_EXPENSE_REPORT_DB:
            if report["guid"] == guid and report["status"] == "SUBMITTED":
                report["status"] = obj_in.status
                report["reviewed_at"] = datetime.utcnow().isoformat() + "Z"
                report["reviewer_guid"] = reviewer_guid
                if obj_in.notes:
                    report["notes"] = obj_in.notes
                logger.info(f"费用报告 {guid} 已被审批为 {obj_in.status}")
                return report
        return None

    async def delete_expense_report(self, db: AsyncSession, *, guid: str) -> Optional[Dict[str, Any]]:
        """【真实模式】删除费用报告"""
        # 【注意】此操作不涉及数据库，因此无需添加数据库异常处理
        for i, report in enumerate(MOCK_EXPENSE_REPORT_DB):
            if report["guid"] == guid:
                deleted_report = MOCK_EXPENSE_REPORT_DB.pop(i)
                logger.info(f"费用报告 {guid} 已被删除")
                return deleted_report
        return None

    async def _get_or_create_system_employee(self, db: AsyncSession) -> Optional[Employee]:
        """获取或创建系统员工，此方法具备完整的数据库事务安全。"""
        stmt = select(Employee).where(Employee.username == SYSTEM_EMPLOYEE_USERNAME)
        try:
            result = await db.execute(stmt)
            employee = result.scalar_one_or_none()
            if employee:
                logger.info(f"系统员工 '{SYSTEM_EMPLOYEE_USERNAME}' 已存在。")
                return employee

            # 如果不存在，尝试创建
            logger.warning(f"系统员工 '{SYSTEM_EMPLOYEE_USERNAME}' 不存在，正在创建...")
            new_employee = Employee(
                username=SYSTEM_EMPLOYEE_USERNAME,
                hashed_password='$2b$12$THIS.IS.A.SYSTEM.USER.PASSWORD.SALT',
                acl='["read"]',  # 给予只读权限
                active=True
            )
            db.add(new_employee)
            await db.commit()
            await db.refresh(new_employee)
            logger.info(f"成功创建系统员工: {new_employee.username} (GUID: {new_employee.guid})")
            return new_employee

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"创建系统员工 '{SYSTEM_EMPLOYEE_USERNAME}' 失败: {e}")
            # 在并发情况下，可能是其他进程已经创建了，所以再次尝试获取
            try:
                result = await db.execute(stmt)
                return result.scalar_one_or_none()
            except SQLAlchemyError as final_e:
                logger.error(f"回滚后再次获取系统员工也失败: {final_e}")
                return None


# 实例化
crud_expense = CRUDExpense()
