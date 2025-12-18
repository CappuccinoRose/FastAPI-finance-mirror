# app/crud/crud_account.py
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.crud.base import CRUDBase
from app.models import Transaction
from app.models.account import Account
from app.models.split import Split
from app.schemas.account import AccountCreate, AccountUpdate


class CRUDAccount(CRUDBase[Account, AccountCreate, AccountUpdate]):
    async def get_root_accounts(self, db: AsyncSession) -> List[Account]:
        """获取所有顶级账户（没有父账户的账户）。"""
        try:
            statement = select(Account).where(Account.parent_guid.is_(None))
            result = await db.execute(statement)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching root accounts: {e}")
            return []

    async def get_children(self, db: AsyncSession, parent_guid: str) -> List[Account]:
        """获取指定父账户下的所有直接子账户。"""
        try:
            statement = select(Account).where(Account.parent_guid == parent_guid)
            result = await db.execute(statement)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching children for parent {parent_guid}: {e}")
            return []

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Account]:
        """通过名称获取单个账户。"""
        try:
            statement = select(Account).where(Account.name == name)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error fetching account by name {name}: {e}")
            return None

    async def get_by_type(
            self, db: AsyncSession, *, account_type: str
    ) -> Optional[Account]:
        """
        通过账户类型获取单个账户。
        注意：如果存在多个同类型的账户，此方法只返回第一个。
        """
        try:
            statement = select(Account).where(Account.account_type == account_type)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error fetching account by type {account_type}: {e}")
            return None

    async def get_multi_by_type(
            self, db: AsyncSession, *, account_types: List[str]
    ) -> List[Account]:
        """根据一个或多个账户类型列表获取所有匹配的账户。"""
        try:
            statement = select(Account).where(Account.account_type.in_(account_types))
            result = await db.execute(statement)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching accounts by types {account_types}: {e}")
            return []

    async def get_balance(
            self, db: AsyncSession, *, account_guid: str, before_date: Optional[str] = None
    ) -> float:
        """
        计算指定科目在指定日期前的余额。
        余额 = 所有贷方分录之和 - 所有借方分录之和
        """
        try:
            # 构建基础查询，计算该科目的总借贷金额
            # 使用 CASE WHEN 更清晰地表达借贷逻辑
            statement = (
                select(
                    func.sum(
                        func.case(
                            (Split.value > 0, Split.value),
                            else_=0
                        )
                    ).label("total_credit"),
                    func.sum(
                        func.case(
                            (Split.value < 0, Split.value),
                            else_=0
                        )
                    ).label("total_debit")
                )
                .join(Transaction, Split.txn_guid == Transaction.guid)
                .where(Split.account_guid == account_guid)
            )

            # 如果指定了截止日期，则添加过滤条件
            if before_date:
                try:
                    cutoff_datetime = datetime.strptime(before_date, "%Y-%m-%d")
                except ValueError:
                    raise ValueError("日期格式错误，应为 YYYY-MM-DD")
                statement = statement.where(Transaction.post_date <= cutoff_datetime)

            result = await db.execute(statement)
            row = result.first()

            # 使用 .getattr 安全地获取可能为 None 的值
            credit_sum = getattr(row, 'total_credit', 0.0) or 0.0
            debit_sum = getattr(row, 'total_debit', 0.0) or 0.0

            # 余额 = 贷方 - 借方
            # debit_sum 本身是负数，所以直接相加即可
            balance = credit_sum + debit_sum
            return round(balance, 2)

        except SQLAlchemyError as e:
            print(f"Error calculating balance for account {account_guid}: {e}")
            return 0.0  # 发生错误时返回 0.0 是一个安全的默认值


crud_account = CRUDAccount(Account)
