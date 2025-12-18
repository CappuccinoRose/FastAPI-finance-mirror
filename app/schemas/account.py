from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.schemas.account import Account

class AccountBase(BaseModel):
    name: str = Field(..., max_length=255)
    account_type: str = Field(..., max_length=50)
    parent_guid: Optional[str] = None
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    hidden: bool = False
    placeholder: bool = False

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    account_type: Optional[str] = Field(None, max_length=50)
    parent_guid: Optional[str] = None
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    hidden: Optional[bool] = None
    placeholder: Optional[bool] = None

class Account(AccountBase):
    guid: str
    parent_guid: Optional[str] = None

    class Config:
        from_attributes = True
