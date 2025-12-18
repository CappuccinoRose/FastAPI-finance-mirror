# app/api/v1/endpoints/period_closing.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.core.period_closing_logic import perform_income_expense_closing
from app.crud import crud_period_closing
from app.db.session import AsyncSessionLocal
from app.schemas.period_closing import PeriodClosing, PeriodClosingCreate
from app.schemas.user import UserWithAuth

router = APIRouter()


# 一个辅助函数，用于在后台任务中获取独立的数据库会话
async def get_db_for_background_task():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@router.post("/", response_model=PeriodClosing, summary="发起期末结转任务")
async def create_period_closing_task(
    *,
    db: AsyncSession = Depends(get_db), # 这个 db session 只用于创建任务
    background_tasks: BackgroundTasks,
    obj_in: PeriodClosingCreate,
    current_user: UserWithAuth = Depends(get_current_active_user)
):
    """
    发起一个期末结转任务（如结转损益）。
    - 任务会立即被创建，状态为 'pending'。
    - 实际的结转计算和凭证生成将在后台异步执行。
    - 需要管理员权限。
    """
    if current_user.acl != "admin":
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以执行期末结转。")
    db_obj = await crud_period_closing.create_closing_task(db=db, obj_in=obj_in)
    background_tasks.add_task(
        perform_income_expense_closing,
        task_guid=db_obj.guid,
        period_end_date=obj_in.period_end_date.isoformat()
    )
    return db_obj


@router.get("/", response_model=List[PeriodClosing], summary="获取期末结转任务历史")
async def read_period_closings(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserWithAuth = Depends(get_current_active_user)
):
    """
    获取所有期末结转任务的历史列表，按创建时间倒序排列。
    """
    closings = await crud_period_closing.get_multi(db=db, skip=skip, limit=limit)
    return closings


@router.get("/{task_guid}", response_model=PeriodClosing, summary="获取单个期末结转任务详情")
async def read_period_closing_task(
    *,
    db: AsyncSession = Depends(get_db),
    task_guid: str,
    current_user: UserWithAuth = Depends(get_current_active_user)
):
    """
    根据 GUID 获取单个期末结转任务的详细状态和结果凭证。
    """
    closing_task = await crud_period_closing.get(db=db, guid=task_guid)
    if not closing_task:
        raise HTTPException(status_code=404, detail="未找到该结转任务")
    return closing_task

