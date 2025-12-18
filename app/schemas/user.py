# app/schemas/user.py
from pydantic import BaseModel, EmailStr

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    guid: str
    username: str
    full_name: str | None = None
    email: str | None = None
    active: bool

    class Config:
        from_attributes = True

class UserWithAuth(User):
    acl: str | None = None # 添加权限字段

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str


class PasswordResetRequest(BaseModel):
    username: str


class PasswordResetResponse(BaseModel):
    reset_code: str


class PasswordResetConfirm(BaseModel):
    username: str
    reset_code: str
    new_password: str
