# app/api/v1/endpoints/accounts_payable.py
from typing import List, Optional

from app.api.v1.deps import get_current_active_user, get_db
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app import schemas
from app.core.exceptions import ConflictException, NotFoundException
from app.crud import crud_purchase_bill
from app.crud import crud_vendor
from app.schemas.purchase_bill import (
    PurchaseBill,
    PurchaseBillCreate,
    PurchaseBillUpdate,
    PurchaseBillSummary
)
from app.schemas.user import User

router = APIRouter()

@router.get("/vendors/", response_model=List[schemas.Vendor], summary="获取供应商列表")
async def read_vendors(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_active_user)
):
    return await crud_vendor.get_multi(db, skip=skip, limit=limit)


@router.post("/vendors/", response_model=schemas.Vendor, summary="创建新供应商", status_code=status.HTTP_201_CREATED)
async def create_vendor(
        *,
        db: AsyncSession = Depends(get_db),
        vendor_in: schemas.VendorCreate,
        current_user: User = Depends(get_current_active_user)
):
    vendor = await crud_vendor.get_by_name(db, name=vendor_in.name)
    if vendor:
        raise ConflictException(detail="供应商已存在")
    return await crud_vendor.create(db=db, obj_in=vendor_in)


@router.patch("/vendors/{guid}", response_model=schemas.Vendor, summary="根据 GUID 部分更新供应商")
async def update_vendor(
        *,
        db: AsyncSession = Depends(get_db),
        guid: str,
        vendor_in: schemas.VendorUpdate,
        current_user: User = Depends(get_current_active_user)
):
    vendor = await crud_vendor.get(db=db, id=guid)
    if not vendor:
        raise NotFoundException(detail="供应商未找到")
    return await crud_vendor.update(db=db, db_obj=vendor, obj_in=vendor_in)


@router.delete("/vendors/{guid}", response_model=schemas.Vendor, summary="根据 GUID 删除供应商")
async def delete_vendor(
        *,
        db: AsyncSession = Depends(get_db),
        guid: str,
        current_user: User = Depends(get_current_active_user)
):
    vendor = await crud_vendor.get(db=db, id=guid)
    if not vendor:
        raise NotFoundException(detail="供应商未找到")
    await crud_vendor.remove(db=db, id=guid)
    return vendor

@router.get("/purchase-bills", response_model=List[PurchaseBillSummary])
async def read_purchase_bills(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = Query(None, description="按状态筛选: draft, confirmed, posted, cancelled"),
        search: Optional[str] = Query(None, description="搜索账单号或供应商名称"),
        current_user: User = Depends(get_current_active_user),
):
    """
    获取采购账单列表，可按状态或关键词筛选
    """
    purchase_bills = await crud_purchase_bill.get_multi(
        db,
        skip=skip,
        limit=limit,
        status=status,
        search=search
    )
    return purchase_bills


@router.post("/purchase-bills", response_model=PurchaseBill, status_code=status.HTTP_201_CREATED)
async def create_purchase_bill(
        *,
        db: AsyncSession = Depends(get_db),
        bill_in: PurchaseBillCreate,
        current_user: User = Depends(get_current_active_user),
):
    """
    创建新的采购账单
    """
    bill = await crud_purchase_bill.get_by_bill_number(db, bill_number=bill_in.bill_number)
    if bill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该账单号已存在"
        )
    return await crud_purchase_bill.create_with_vendor(db, obj_in=bill_in)


@router.get("/purchase-bills/{guid}", response_model=PurchaseBillSummary)
async def read_purchase_bill(
        *,
        db: AsyncSession = Depends(get_db),
        guid: str,
        current_user: User = Depends(get_current_active_user),
):
    """
    获取单个采购账单详情
    """

    statement = select(crud_purchase_bill.model).options(selectinload(crud_purchase_bill.model.vendor)).where(crud_purchase_bill.model.guid == guid)
    result = await db.execute(statement)
    bill = result.scalar_one_or_none()

    if not bill:
        raise HTTPException(status_code=404, detail="采购账单未找到")
    return bill


@router.put("/purchase-bills/{guid}", response_model=PurchaseBill)
async def update_purchase_bill(
        *,
        db: AsyncSession = Depends(get_db),
        guid: str,
        bill_in: PurchaseBillUpdate,
        current_user: User = Depends(get_current_active_user),
):
    """
    更新采购账单信息
    """
    bill = await crud_purchase_bill.get(db, id=guid)
    if not bill:
        raise HTTPException(status_code=404, detail="采购账单未找到")

    if bill_in.bill_number and bill_in.bill_number != bill.bill_number:
        existing_bill = await crud_purchase_bill.get_by_bill_number(db, bill_number=bill_in.bill_number)
        if existing_bill:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该账单号已存在"
            )

    if bill.status == "posted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已过账的账单不能修改"
        )

    return await crud_purchase_bill.update(db, db_obj=bill, obj_in=bill_in)


@router.delete("/purchase-bills/{guid}", response_model=PurchaseBill)
async def delete_purchase_bill(
        *,
        db: AsyncSession = Depends(get_db),
        guid: str,
        current_user: User = Depends(get_current_active_user),
):
    """
    删除采购账单
    """
    bill = await crud_purchase_bill.get(db, id=guid)
    if not bill:
        raise HTTPException(status_code=404, detail="采购账单未找到")

    # Prevent deleting a posted bill
    if bill.status == "posted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已过账的账单不能删除"
        )

    return await crud_purchase_bill.remove(db, id=guid)


@router.post("/purchase-bills/{guid}/post", response_model=PurchaseBill)
async def post_purchase_bill(
        *,
        db: AsyncSession = Depends(get_db),
        guid: str,
        current_user: User = Depends(get_current_active_user),
):
    """
    过账采购账单
    """
    bill = await crud_purchase_bill.get(db, id=guid)
    if not bill:
        raise HTTPException(status_code=404, detail="采购账单未找到")

    if bill.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有已确认的账单才能过账"
        )

    if bill.post_txn_guid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该账单已经过账"
        )

    # TODO: Implement actual posting logic (create transaction and splits)
    # For now, we'll just update the status
    bill_update = PurchaseBillUpdate(status="posted")
    return await crud_purchase_bill.update(db, db_obj=bill, obj_in=bill_update)


@router.post("/purchase-bills/{guid}/cancel", response_model=PurchaseBill)
async def cancel_purchase_bill(
        *,
        db: AsyncSession = Depends(get_db),
        guid: str,
        current_user: User = Depends(get_current_active_user),
):
    """
    取消采购账单
    """
    bill = await crud_purchase_bill.get(db, id=guid)
    if not bill:
        raise HTTPException(status_code=404, detail="采购账单未找到")

    if bill.status == "posted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已过账的账单不能取消"
        )

    if bill.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该账单已经取消"
        )

    bill_update = PurchaseBillUpdate(status="cancelled")
    return await crud_purchase_bill.update(db, db_obj=bill, obj_in=bill_update)


