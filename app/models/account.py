# app/models/account.py
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4
from typing import TYPE_CHECKING
from app.db.base import Base

# 将跨模型导入移入 TYPE_CHECKING 块
if TYPE_CHECKING:
    from app.models.split import Split


class Account(Base):
    __tablename__ = "accounts"

    guid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_guid: Mapped[str | None] = mapped_column(String(36), ForeignKey("accounts.guid", ondelete="SET NULL"))
    code: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(255))
    hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    placeholder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    # 自引用关系，不需要导入其他模型，所以可以直接使用字符串
    parent: Mapped["Account"] = relationship("Account", remote_side=[guid], back_populates="children")
    children: Mapped[list["Account"]] = relationship("Account", back_populates="parent", cascade="all, delete-orphan",
                                                     lazy="raise")

    # 与 Split 的关系，使用字符串引用
    splits: Mapped[list["Split"]] = relationship("Split", back_populates="account", lazy="raise")
