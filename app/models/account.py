# app/models/account.py
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4
from app.db.base import Base


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
    parent: Mapped["Account"] = relationship("Account", remote_side=[guid], back_populates="children")
    # 将 lazy="raise" 添加到 children 关系，以防止意外的同步查询
    children: Mapped[list["Account"]] = relationship("Account", back_populates="parent", cascade="all, delete-orphan", lazy="raise")
    splits: Mapped[list["Split"]] = relationship("Split", back_populates="account", lazy="raise") # 同样为 splits 添加 lazy="raise"
