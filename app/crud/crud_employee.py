# app/crud/crud_employee.py
from typing import Any, Dict, Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class CRUDEmployee(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[Employee]:
        """通过用户名获取员工对象。"""
        try:
            statement = select(Employee).where(Employee.username == username)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error fetching employee by username '{username}': {e}")
            return None

    async def create(self, db: AsyncSession, *, obj_in: EmployeeCreate) -> Optional[Employee]:
        """
        创建新员工。此方法会自动处理密码哈希。
        """
        try:
            db_obj = Employee(
                username=obj_in.username,
                hashed_password=get_password_hash(obj_in.password),
                id=obj_in.id,
                language=obj_in.language,
                active=obj_in.active,
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating employee '{obj_in.username}': {e}")
            return None

    async def create_with_password(
        self, db: AsyncSession, *, username: str, password: str, **extra_fields
    ) -> Optional[Employee]:
        """
        通过直接提供用户名和密码来创建员工。
        """
        try:
            hashed_password = get_password_hash(password)
            db_obj = Employee(
                username=username,
                hashed_password=hashed_password,
                **extra_fields
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating employee with username '{username}': {e}")
            return None

    async def authenticate(
            self, db: AsyncSession, *, username: str, password: str
    ) -> Optional[Employee]:
        """
        验证用户名和密码，返回用户对象或 None。
        """
        user = await self.get_by_username(db, username=username)
        if not user:
            return None
        if not user.active:
            # 用户存在但已被禁用
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Employee,
        obj_in: Union[EmployeeUpdate, Dict[str, Any]]
    ) -> Optional[Employee]:
        """
        更新员工信息。如果更新数据中包含 'password'，则会自动进行哈希处理。
        """
        try:
            update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

            password_to_update = update_data.pop("password", None)
            if password_to_update:
                db_obj.hashed_password = get_password_hash(password_to_update)

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating employee '{db_obj.username}': {e}")
            return None

crud_employee = CRUDEmployee(Employee)
