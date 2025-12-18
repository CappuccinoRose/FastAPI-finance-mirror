# app/core/period_closing_logic.py

import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.crud.crud_account import crud_account
from app.crud.crud_period_closing import crud_period_closing
from app.crud.crud_split import crud_split
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.period_closing import PeriodClosingUpdate
from app.core.exceptions import BusinessException
from app.db.session import AsyncSessionLocal  # 【新增】导入 SessionLocal

# 设置日志
logger = logging.getLogger(__name__)

# --- 会计科目类型常量 ---
INCOME_TYPES = ['INCOME', 'REVENUE']
EXPENSE_TYPES = ['EXPENSE']
EQUITY_TYPES = ['EQUITY']

# 结转损益的目标科目（本年利润）
PROFIT_AND_LOSS_ACCOUNT_GUID = "acc-profit-loss-guid"  # <--- 【重要】请确认这个 GUID 是否正确


async def perform_income_expense_closing(
        task_guid: str,
        period_end_date: str
) -> Transaction:
    """
    执行结转损益的后台任务。
    此函数会自己创建和管理数据库会话。
    """
    async with AsyncSessionLocal() as db:
        logger.info(f"开始执行结转损益任务，任务 GUID: {task_guid}, 期间截止: {period_end_date}")

        # 1. 获取结转任务对象
        closing_task = await crud_period_closing.get(db=db, guid=task_guid)
        if not closing_task:
            logger.error(f"结转任务 {task_guid} 未找到！")
            raise BusinessException("结转任务未找到")

        # 2. 更新任务状态为 'in_progress'
        await crud_period_closing.update_closing_transaction(
            db, db_obj=closing_task, status="in_progress"
        )
        logger.info(f"任务 {task_guid} 状态已更新为 'in_progress'")

        try:
            # 3. 获取所有需要结转的科目（收入和费用）
            income_accounts = await crud_account.get_multi_by_type(db, account_types=INCOME_TYPES)
            expense_accounts = await crud_account.get_multi_by_type(db, account_types=EXPENSE_TYPES)

            closing_accounts = income_accounts + expense_accounts
            if not closing_accounts:
                logger.warning(f"期间 {period_end_date} 内没有找到需要结转的损益科目。")
                await crud_period_closing.update_closing_transaction(
                    db, db_obj=closing_task, status="completed"
                )
                return closing_task

            # 4. 计算每个科目的余额并准备结转分录
            splits_to_create = []
            total_income = 0.0
            total_expense = 0.0

            for account in closing_accounts:
                balance = await crud_account.get_balance(db, account_guid=account.guid, before_date=period_end_date)

                if abs(balance) < 0.01:
                    continue

                if account.account_type in INCOME_TYPES:
                    value = -balance
                    total_income += balance
                else:  # EXPENSE_TYPES
                    value = -balance
                    total_expense += -balance

                splits_to_create.append({
                    "guid": str(uuid4()),
                    "account_guid": account.guid,
                    "memo": f"结转 {account.name} 至 {period_end_date}",
                    "value": value,
                    "quantity_num": 1,
                    "quantity_denom": 1,
                    "reconcile_state": 'n',
                })

            # 5. 创建“本年利润”科目的结转分录
            net_profit = total_income - total_expense
            if net_profit != 0:
                splits_to_create.append({
                    "guid": str(uuid4()),
                    "account_guid": PROFIT_AND_LOSS_ACCOUNT_GUID,
                    "memo": f"本期净利润 (截至 {period_end_date})",
                    "value": net_profit,
                    "quantity_num": 1,
                    "quantity_denom": 1,
                    "reconcile_state": 'n',
                })

            # 6. 检查借贷是否平衡
            total_value = sum(s['value'] for s in splits_to_create)
            if abs(total_value) > 0.01:
                raise BusinessException(f"结转分录借贷不平衡，差额: {total_value}。请检查科目余额计算。")

            # 7. 更新结转任务，标记为完成，并保存分录
            await crud_period_closing.update_closing_transaction(
                db,
                db_obj=closing_task,
                status="completed",
                splits_to_create=splits_to_create
            )
            logger.info(f"结转损益任务 {task_guid} 已成功完成。共生成 {len(splits_to_create)} 条分录。")

            await db.refresh(closing_task)
            return closing_task

        except Exception as e:
            logger.error(f"执行结转损益任务 {task_guid} 时发生错误: {e}", exc_info=True)
            # 8. 如果发生任何错误，更新任务状态为 'failed'
            await crud_period_closing.update_closing_transaction(
                db,
                db_obj=closing_task,
                status="failed",
                error_message=str(e)
            )
            raise
