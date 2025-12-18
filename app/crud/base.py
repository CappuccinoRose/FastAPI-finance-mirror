# app/crud/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sql_update, delete as sql_delete
from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base

# 泛型类型定义
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    带有默认方法的 CRUD 对象基类。
    """

    def __init__(self, model: Type[ModelType]):
        """
        CRUD 对象带有用于数据库操作的默认方法。
        **参数**
        * `model`: 一个 SQLAlchemy 模型类
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        通过 ID 获取单个记录。
        """
        try:
            statement = select(self.model).where(self.model.guid == id)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            # 在实际应用中，这里应该记录日志
            print(f"Error getting {self.model.__name__} by id {id}: {e}")
            return None

    async def get_multi(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        获取多个记录，支持分页。
        """
        try:
            statement = select(self.model).offset(skip).limit(limit)
            result = await db.execute(statement)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error getting multiple {self.model.__name__}: {e}")
            return []

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> Optional[ModelType]:
        """
        创建一个新记录。
        """
        try:
            # Pydantic v2 的 model_dump() 是 jsonable_encoder 的现代替代品
            obj_in_data = obj_in.model_dump()
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating {self.model.__name__}: {e}")
            return None

    async def update(
            self,
            db: AsyncSession,
            *,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        """
        更新一个记录。
        """
        try:
            # 如果 obj_in 是 Pydantic 模型，则转换为字典，并排除未设置的字段
            update_data = obj_in.model_dump(exclude_unset=True) if not isinstance(obj_in, dict) else obj_in

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating {self.model.__name__}: {e}")
            return None

    async def remove(self, db: AsyncSession, *, id: str) -> Optional[ModelType]:
        """
        通过 ID 删除一个记录。
        """
        try:
            obj = await self.get(db, id=id)
            if obj:
                await db.delete(obj)
                await db.commit()
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error removing {self.model.__name__} with id {id}: {e}")
            return None

    async def exists(self, db: AsyncSession, *, id: Any) -> bool:
        """
        检查具有给定 ID 的记录是否存在。
        这是一个高效的检查，只查询 COUNT(1) 而不获取实际数据。
        """
        try:
            statement = select(self.model).where(self.model.guid == id).exists()
            result = await db.execute(statement)
            return result.scalar()
        except SQLAlchemyError as e:
            print(f"Error checking existence of {self.model.__name__} with id {id}: {e}")
            return False

