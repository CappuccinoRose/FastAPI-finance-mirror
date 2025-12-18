# app/crud/crud_vendor.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.crud.base import CRUDBase
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate


class CRUDVendor(CRUDBase[Vendor, VendorCreate, VendorUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Vendor]:
        """通过供应商名称获取单个供应商。"""
        try:
            statement = select(Vendor).where(Vendor.name == name)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error fetching vendor by name '{name}': {e}")
            return None

crud_vendor = CRUDVendor(Vendor)
