# app/schemas/base.py
from pydantic import BaseModel

class SchemaBase(BaseModel):
    """所有Schema的基类，包含共有的guid字段。"""
    guid: str

    class Config:
        # Pydantic V2 的配置，允许从ORM对象（SQLAlchemy模型）创建Pydantic模型实例
        from_attributes = True
