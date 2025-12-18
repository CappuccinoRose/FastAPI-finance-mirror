# app/crud/crud_split.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.crud.base import CRUDBase
from app.models.split import Split
from app.schemas import SplitCreate, SplitUpdate


class CRUDSplit(CRUDBase[Split, SplitCreate, SplitUpdate]):
    async def get_by_transaction(self, db: AsyncSession, *, txn_guid: str) -> List[Split]:
        """获取指定交易下的所有分录。"""
        try:
            statement = select(Split).where(Split.txn_guid == txn_guid)
            result = await db.execute(statement)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching splits for transaction '{txn_guid}': {e}")
            return []

    async def get_by_account(self, db: AsyncSession, *, account_guid: str) -> List[Split]:
        """获取指定账户下的所有分录。"""
        try:
            statement = select(Split).where(Split.account_guid == account_guid)
            result = await db.execute(statement)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching splits for account '{account_guid}': {e}")
            return []

crud_split = CRUDSplit(Split)
