# app/crud/crud_entry.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.crud.base import CRUDBase
from app.models.entry import Entry
from app.schemas import EntryCreate, EntryUpdate


class CRUDEntry(CRUDBase[Entry, EntryCreate, EntryUpdate]):
    async def get_by_invoice(self, db: AsyncSession, *, invoice_guid: str) -> List[Entry]:
        """获取指定发票GUID下的所有条目。"""
        try:
            statement = select(Entry).where(Entry.invoice_guid == invoice_guid)
            result = await db.execute(statement)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching entries for invoice '{invoice_guid}': {e}")
            return []

crud_entry = CRUDEntry(Entry)
