# app/crud/crud_purchase_bill.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.crud.base import CRUDBase
from app.models.purchase_bill import PurchaseBill
from app.models.vendor import Vendor
from app.schemas.purchase_bill import PurchaseBillCreate, PurchaseBillUpdate


class CRUDPurchaseBill(CRUDBase[PurchaseBill, PurchaseBillCreate, PurchaseBillUpdate]):
    async def get_by_bill_number(self, db: AsyncSession, *, bill_number: str) -> Optional[PurchaseBill]:
        """通过账单号获取单个采购账单。"""
        try:
            statement = select(PurchaseBill).where(PurchaseBill.bill_number == bill_number)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error fetching purchase bill by number '{bill_number}': {e}")
            return None

    async def get_by_status(
            self, db: AsyncSession, *, status: str, skip: int = 0, limit: int = 100
    ) -> List[PurchaseBill]:
        """根据状态获取采购账单列表。"""
        try:
            statement = (
                select(PurchaseBill)
                .options(selectinload(PurchaseBill.vendor))
                .where(PurchaseBill.status == status)
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(statement)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching purchase bills by status '{status}': {e}")
            return []

    async def get_multi(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100, status: Optional[str] = None,
            search: Optional[str] = None
    ) -> List[PurchaseBill]:
        """
        获取采购账单列表，支持按状态筛选和关键词搜索。
        关键词会搜索账单号和供应商名称。
        """
        try:
            # 【关键修正】当需要在 WHERE 条件中使用关联表的字段时，应使用 joinedload
            statement = select(PurchaseBill).options(
                selectinload(PurchaseBill.vendor), # 用于最终结果加载
                joinedload(PurchaseBill.vendor)    # 用于 WHERE 条件中的 Vendor.name
            )

            if status:
                statement = statement.where(PurchaseBill.status == status)

            if search:
                search_filter = or_(
                    PurchaseBill.bill_number.ilike(f"%{search}%"),
                    Vendor.name.ilike(f"%{search}%")
                )
                statement = statement.where(search_filter)

            statement = statement.offset(skip).limit(limit).order_by(PurchaseBill.bill_date.desc())

            result = await db.execute(statement)
            # 使用 .unique() 来去重，因为 joinedload 可能会导致主实体重复
            return result.scalars().unique().all()
        except SQLAlchemyError as e:
            print(f"Error fetching purchase bills with filters: {e}")
            return []

    async def create_with_vendor(self, db: AsyncSession, *, obj_in: PurchaseBillCreate) -> Optional[PurchaseBill]:
        """
        创建采购账单的便捷方法。
        实际创建逻辑由父类的 create 方法处理。
        """
        # 调用父类的 create 方法，它已经包含了错误处理和事务安全
        return await super().create(db, obj_in=obj_in)


crud_purchase_bill = CRUDPurchaseBill(PurchaseBill)
