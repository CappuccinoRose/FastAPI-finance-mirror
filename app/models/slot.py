# app/models/slot.py
from sqlalchemy import String, TEXT, NUMERIC
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Slot(Base):
    __tablename__ = "slots"

    obj_guid: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    slot_type: Mapped[str] = mapped_column(String(50), nullable=False)
    string_val: Mapped[str | None] = mapped_column(TEXT)
    numeric_val: Mapped[float | None] = mapped_column(NUMERIC(precision=18, scale=2))

    def __repr__(self):
        return (f"<Slot(obj_guid='{self.obj_guid}', name='{self.name}', "
                f"slot_type='{self.slot_type}', string_val='{self.string_val}', "
                f"numeric_val={self.numeric_val})>")
