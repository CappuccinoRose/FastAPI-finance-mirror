# app/api/v1/endpoints/general_ledger.py
# 会计科目等内容
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app import schemas
from app.api.v1 import deps
from app.crud import crud_account, crud_transaction, crud_split
from app.schemas.user import User
from app.models.split import Split
from app.core.exceptions import NotFoundException, ConflictException, BusinessException

router = APIRouter()

@router.get("/", response_model=List[schemas.Account], summary="获取科目列表")
async def read_accounts(
        db: AsyncSession = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        parent_guid: Optional[str] = Query(None, description="父科目GUID，为空则查询根科目"),
        current_user: User = Depends(deps.get_current_active_user)
):
    if parent_guid is None:
        accounts = await crud_account.get_root_accounts(db)
    else:
        accounts = await crud_account.get_children(db, parent_guid=parent_guid)
    return accounts


@router.post("/", response_model=schemas.Account, summary="创建新科目", status_code=status.HTTP_201_CREATED)
async def create_account(
        *,
        db: AsyncSession = Depends(deps.get_db),
        account_in: schemas.AccountCreate,
        current_user: User = Depends(deps.get_current_active_user)
):
    account = await crud_account.get_by_name(db, name=account_in.name)
    if account:
        raise ConflictException(detail="系统中已存在同名科目。")
    return await crud_account.create(db=db, obj_in=account_in)


@router.get("/{guid}", response_model=schemas.Account, summary="根据GUID获取科目")
async def read_account(
        *,
        db: AsyncSession = Depends(deps.get_db),
        guid: str,
        current_user: User = Depends(deps.get_current_active_user)
):
    account = await crud_account.get(db=db, id=guid)
    if not account:
        raise NotFoundException(detail="未找到该科目")
    return account


@router.put("/{guid}", response_model=schemas.Account, summary="更新科目")
async def update_account(
        *,
        db: AsyncSession = Depends(deps.get_db),
        guid: str,
        account_in: schemas.AccountUpdate,
        current_user: User = Depends(deps.get_current_active_user)
):
    account = await crud_account.get(db=db, id=guid)
    if not account:
        raise NotFoundException(detail="未找到该科目")
    return await crud_account.update(db=db, db_obj=account, obj_in=account_in)


@router.get("/transactions", response_model=List[schemas.Transaction], summary="获取交易列表")
async def read_transactions(
        db: AsyncSession = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(deps.get_current_active_user)
):
    return await crud_transaction.get_multi(db, skip=skip, limit=limit)


@router.post("/transactions", response_model=schemas.Transaction, summary="创建新交易",
             status_code=status.HTTP_201_CREATED)
async def create_transaction(
        *,
        db: AsyncSession = Depends(deps.get_db),
        transaction_in: schemas.TransactionCreate,
        current_user: User = Depends(deps.get_current_active_user)
):
    try:
        async with db.begin():
            transaction_data = transaction_in.model_dump(exclude={"splits"})
            db_transaction = await crud_transaction.create(db, obj_in=transaction_data)

            if transaction_in.splits:
                split_objects = []
                for split_in in transaction_in.splits:
                    split_data = split_in.model_dump()
                    split_data["txn_guid"] = db_transaction.guid
                    split_objects.append(Split(**split_data))
                db.add_all(split_objects)

            await db.refresh(db_transaction)
            return db_transaction

    except IntegrityError as e:
        raise BusinessException(detail="创建交易失败，数据不完整或存在冲突。") from e
    except Exception as e:
        raise BusinessException(detail="服务器内部错误。", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e


@router.get("/transactions/{guid}", response_model=schemas.Transaction, summary="根据GUID获取交易")
async def read_transaction(
        *,
        db: AsyncSession = Depends(deps.get_db),
        guid: str,
        current_user: User = Depends(deps.get_current_active_user)
):
    transaction = await crud_transaction.get(db=db, id=guid)
    if not transaction:
        raise NotFoundException(detail="未找到该交易")
    return transaction
