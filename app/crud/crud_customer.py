# app/crud/crud_customer.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.crud.base import CRUDBase
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Customer]:
        """通过客户名称查找客户。"""
        try:
            statement = select(Customer).where(Customer.name == name)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error fetching customer by name '{name}': {e}")
            return None

    async def get_by_id(self, db: AsyncSession, *, id: str) -> Optional[Customer]:
        """
        根据自定义ID（如税号）查找客户。
        注意：此 'id' 不同于数据库主键 'guid'。
        """
        try:
            statement = select(Customer).where(Customer.id == id)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error fetching customer by custom id '{id}': {e}")
            return None

crud_customer = CRUDCustomer(Customer)
