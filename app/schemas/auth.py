# app/schemas/auth.py
from pydantic import BaseModel

# 请求密码重置码的请求体
class PasswordResetRequest(BaseModel):
    username: str

# 请求密码重置码的响应体
class PasswordResetResponse(BaseModel):
    reset_code: str

# 确认重置密码的请求体
class PasswordResetConfirm(BaseModel):
    username: str
    reset_code: str
    new_password: str
