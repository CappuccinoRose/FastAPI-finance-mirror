# app/crud/crud_period_closing.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.models.transaction import Transaction
from app.schemas.period_closing import PeriodClosingCreate, PeriodClosingUpdate


class CRUDPeriodClosing:
    """
    专门用于从 transactions 表中查询结转任务的 CRUD 操作。
    """

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """
        获取所有结转任务，按 enter_date 倒序排列。
        使用 selectinload 预加载关联的 splits，避免序列化时的 N+1 查询。
        """
        try:
            statement = (
                select(Transaction)
                .options(selectinload(Transaction.splits))
                .where(Transaction.description.like("[CLOSING-TASK]%"))
                .order_by(Transaction.enter_date.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(statement)
            return result.scalars().unique().all()
        except SQLAlchemyError as e:
            print(f"Error fetching period closing tasks: {e}")
            return []

    async def get(
        self, db: AsyncSession, *, guid: str
    ) -> Optional[Transaction]:
        """
        根据 GUID 获取单个结转任务。
        同样使用 selectinload 预加载 splits。
        """
        try:
            statement = (
                select(Transaction)
                .options(selectinload(Transaction.splits))
                .where(
                    and_(
                        Transaction.guid == guid,
                        Transaction.description.like("[CLOSING-TASK]%")
                    )
                )
            )
            result = await db.execute(statement)
            return result.scalars().unique().first()
        except SQLAlchemyError as e:
            print(f"Error fetching period closing task by guid '{guid}': {e}")
            return None


# 创建一个全局的 CRUD 实例供其他模块调用
crud_period_closing = CRUDPeriodClosing()

