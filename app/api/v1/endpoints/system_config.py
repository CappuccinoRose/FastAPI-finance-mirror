# app/api/v1/endpoints/system_config.py
# 系统配置部分内容
from typing import Any, List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import deps
from app.crud import crud_account, crud_slot
from app.schemas.account import AccountCreate
from app.schemas.slot import SlotCreate

router = APIRouter()


@router.get("/status", summary="检查系统初始化状态")
async def check_initialization_status(
        db: AsyncSession = Depends(deps.get_db)
) -> dict[str, Any]:
    """
    检查系统是否已完成企业账套初始化。
    通过查找是否存在 'ROOT' 类型的账户来判断。
    """
    root_account = await crud_account.get_by_type(db, account_type="ROOT")
    return {"initialized": root_account is not None}


@router.post("/init", summary="初始化企业账套", status_code=status.HTTP_201_CREATED)
async def initialize_enterprise(
        *,
        db: AsyncSession = Depends(deps.get_db),
        # 请求体直接是一个 SlotCreate 对象的列表
        slots_in: List[SlotCreate]
) -> dict[str, Any]:
    """
    执行企业账套的一次性初始化。
    1. 创建一个特殊的 'ROOT' 账户作为挂载点。
    2. 将企业信息存储为与该账户关联的 slots。
    请求体应为一个包含企业信息的 SlotCreate 对象列表。
    """
    # 检查是否已初始化
    root_account = await crud_account.get_by_type(db, account_type="ROOT")
    if root_account:
        raise HTTPException(status_code=409, detail="系统已初始化，无法重复操作。")

    # 1. 创建根科目
    root_account_data = AccountCreate(
        name="企业根科目",
        account_type="ROOT",
        placeholder=True
    )
    created_root_account = await crud_account.create(db=db, obj_in=root_account_data)

    # 2. 为每个 slot 绑定新创建的根科目 GUID，并批量创建
    for slot_in in slots_in:
        slot_in.obj_guid = created_root_account.guid

    await crud_slot.create_multi(db=db, objs_in=slots_in)

    return {"message": "企业账套初始化成功！"}


@router.get("/info", summary="获取系统信息")
async def get_system_info():
    return {
        "version": "1.0.0",
        "python_version": "3.13",
        "status": "running"
    }

