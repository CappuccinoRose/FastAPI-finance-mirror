# app/crud/crud_transaction.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.crud.base import CRUDBase
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: TransactionCreate) -> Optional[Transaction]:
        """
        创建一个新的交易。
        包含业务逻辑校验：确保借贷平衡。
        """
        # 业务逻辑校验：确保借贷平衡
        total_value = sum(split.value for split in obj_in.splits)
        if total_value != 0:
            raise ValueError("交易分录的金额总和必须为零（借贷平衡）。")

        try:
            # 如果校验通过，继续执行父类的创建逻辑
            return await super().create(db, obj_in=obj_in)
        except SQLAlchemyError as e:
            # 父类的 create 已经处理了 rollback，这里只需记录错误或返回 None
            print(f"Error creating transaction: {e}")
            return None

crud_transaction = CRUDTransaction(Transaction)
