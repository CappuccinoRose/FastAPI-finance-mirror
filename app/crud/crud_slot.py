# app/crud/crud_slot.py
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError

from app.crud.base import CRUDBase
from app.models.slot import Slot
from app.schemas.slot import SlotCreate, SlotUpdate


class CRUDSlot(CRUDBase[Slot, SlotCreate, SlotUpdate]):
    async def create_multi(
        self, db: AsyncSession, *, objs_in: List[SlotCreate]
    ) -> List[Slot]:
        """
        批量创建 Slot 记录。这是一个原子操作，如果任何一条记录创建失败，整个批次将回滚。
        """
        try:
            db_objs = [self.model(**obj_in.model_dump()) for obj_in in objs_in]
            db.add_all(db_objs)
            await db.commit()

            await db.refresh(db_objs[0]) # 刷新第一个对象，以获取会话状态

            # SQLAlchemy 会自动将 commit 后的状态同步到内存中的对象
            # 所以我们直接返回 db_objs 即可
            return db_objs
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error during bulk slot creation: {e}")
            return []

    async def get_by_obj_and_name(
        self, db: AsyncSession, *, obj_guid: str, name: str
    ) -> Optional[Slot]:
        """
        根据 obj_guid 和 name 获取单个 Slot。
        """
        try:
            statement = select(self.model).where(
                and_(self.model.obj_guid == obj_guid, self.model.name == name)
            )
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error fetching slot by obj_guid '{obj_guid}' and name '{name}': {e}")
            return None


crud_slot = CRUDSlot(Slot)
