# app/api/v1/endpoints/auth.py
# 登录注册密码重置等内容
import random
import string
from datetime import timedelta
from typing import Any, Union
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas
from app.api.v1 import deps
from app.core import security
from app.core.config import settings
from app.crud.crud_employee import crud_employee
from app.core.exceptions import CredentialsException, InactiveUserException
from app.models.employee import Employee

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=schemas.Token, summary="用户登录获取访问令牌")
async def login_for_access_token(
        db: AsyncSession = Depends(deps.get_db),
        form_data: OAuth2PasswordRequestForm = Depends(),
        request: Request = Depends()
):
    """
    OAuth2兼容的令牌登录，为后续请求获取访问令牌。
    - **username**: 用户名
    - **password**: 密码
    """
    # 尝试从JSON获取数据
    try:
        json_data = await request.json()
        username = json_data.get('username')
        password = json_data.get('password')
    except:
        # 如果不是JSON，使用表单数据
        username = form_data.username
        password = form_data.password

    user = await crud_employee.authenticate(
        db, username=username, password=password
    )
    if not user:
        raise CredentialsException(detail="用户名或密码不正确")

    if not user.active:
        raise InactiveUserException()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED, summary="用户注册")
async def register(
        *,
        db: AsyncSession = Depends(deps.get_db),
        user_in: schemas.UserCreate,
) -> Any:
    """
    注册新用户。
    """
    user = await crud_employee.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="该用户名已被使用",
        )
    user_in_data = user_in.model_dump(exclude_unset=True)
    if "password" in user_in_data:
        del user_in_data["password"]
    user_in_data["hashed_password"] = security.get_password_hash(user_in.password)
    new_user = await crud_employee.create(db, obj_in=user_in_data)

    return new_user


@router.get("/me", response_model=schemas.User, summary="获取当前登录用户信息")
async def read_users_me(
        current_user: Employee = Depends(deps.get_current_user),  # 需要在 deps.py 中实现 get_current_user
) -> Any:
    """
    获取当前登录用户的详细信息。
    """
    return current_user


reset_codes = {}


@router.post("/password-reset/request", response_model=schemas.PasswordResetResponse, summary="请求密码重置码")
async def request_password_reset(
        *,
        db: AsyncSession = Depends(deps.get_db),
        body: schemas.PasswordResetRequest,
) -> Any:
    user = await crud_employee.get_by_username(db, username=body.username)
    if not user:
        return {"reset_code": "如果用户存在，重置码已发送"}
    reset_code = "".join(random.choices(string.ascii_letters + string.digits, k=4))
    reset_codes[user.username] = reset_code
    print(f"DEBUG: Password reset code for {user.username} is {reset_code}")

    return {"reset_code": reset_code}


@router.post("/password-reset/confirm", summary="使用重置码确认新密码")
async def confirm_password_reset(
        *,
        db: AsyncSession = Depends(deps.get_db),
        body: schemas.PasswordResetConfirm,
) -> Any:
    user = await crud_employee.get_by_username(db, username=body.username)
    if not user or reset_codes.get(user.username) != body.reset_code:
        raise HTTPException(status_code=400, detail="无效的重置码或用户名")

    # 更新密码
    user.hashed_password = security.get_password_hash(body.new_password)
    db.add(user)
    await db.commit()

    # 清除重置码
    if user.username in reset_codes:
        del reset_codes[user.username]

    return {"message": "密码重置成功"}
