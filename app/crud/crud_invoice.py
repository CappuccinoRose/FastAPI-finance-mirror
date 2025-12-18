# app/crud/crud_invoice.py
from typing import List, Optional, Union, Dict, Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, BusinessException
from app.crud.base import CRUDBase
from app.models.entry import Entry
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate


class CRUDInvoice(CRUDBase[Invoice, InvoiceCreate, InvoiceUpdate]):
    async def get(self, db: AsyncSession, id: str) -> Optional[Invoice]:
        """
        通过 GUID 获取单个销售发票，并预加载其所有关联数据。
        """
        try:
            statement = (
                select(self.model)
                .options(
                    selectinload(Invoice.customer),
                    selectinload(Invoice.entries).selectinload(Entry.account)
                )
                .where(self.model.guid == id)
            )
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error fetching invoice by id '{id}': {e}")
            return None

    async def get_multi(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Invoice]:
        """
        获取销售发票列表，并预加载其所有关联数据。
        """
        try:
            statement = (
                select(self.model)
                .options(
                    selectinload(Invoice.customer),
                    selectinload(Invoice.entries).selectinload(Entry.account)
                )
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(statement)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching multiple invoices: {e}")
            return []

    async def create(self, db: AsyncSession, *, obj_in: InvoiceCreate) -> Optional[Invoice]:
        """
        创建一个新的销售发票及其明细项。
        这是一个原子操作，如果任何一步失败，整个事务将回滚。
        """
        try:
            # 1. 检查业务ID（发票号）是否已存在
            existing_invoice = await db.execute(select(Invoice).where(Invoice.id == obj_in.id))
            if existing_invoice.scalar_one_or_none():
                raise ConflictException(detail=f"发票号 '{obj_in.id}' 已存在")

            # 2. 准备主表数据
            invoice_data = obj_in.model_dump(exclude={"entries"})
            db_invoice = self.model(**invoice_data)
            db.add(db_invoice)

            # 3. 准备明细表数据
            if obj_in.entries:
                entries_data = [entry.model_dump() for entry in obj_in.entries]
                db_entries = [Entry(**entry_data, invoice_guid=db_invoice.guid) for entry_data in entries_data]
                db.add_all(db_entries)

            # 4. 一次性提交所有更改
            await db.commit()

            # 5. 刷新并返回包含所有关联数据的完整对象
            await db.refresh(db_invoice, ["customer", "entries"])
            # entries 的 account 关系也会因为 refresh 而加载
            return db_invoice

        except ConflictException:
            await db.rollback()
            raise
        except IntegrityError as e:
            await db.rollback()
            raise ConflictException(detail="创建发票失败，数据冲突，请检查输入（如客户是否存在）。") from e
        except SQLAlchemyError as e:
            await db.rollback()
            raise BusinessException(detail="创建发票时发生未知数据库错误。") from e

    async def update(
            self,
            db: AsyncSession,
            *,
            db_obj: Invoice,
            obj_in: Union[InvoiceUpdate, Dict[str, Any]]
    ) -> Optional[Invoice]:
        """
        更新发票信息。
        注意：此方法不处理发票明细项的更新。
        """
        try:
            update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating invoice '{db_obj.guid}': {e}")
            return None

    async def remove(self, db: AsyncSession, *, id: str) -> Optional[Invoice]:
        """
        删除一个发票。
        注意：这可能会因为外键约束而失败，如果有关联的条目存在。
        """
        try:
            obj = await self.get(db, id=id) # 复用 get 方法
            if obj:
                await db.delete(obj)
                await db.commit()
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error removing invoice '{id}': {e}")
            return None


# 实例化 CRUD 对象
crud_invoice = CRUDInvoice(Invoice)
