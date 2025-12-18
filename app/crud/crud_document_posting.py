# app/crud/crud_document_posting.py
from typing import Union
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BusinessException
from app.crud.crud_invoice import crud_invoice
from app.crud.crud_purchase_bill import crud_purchase_bill
from app.models.invoice import Invoice
from app.models.purchase_bill import PurchaseBill
from app.models.split import Split
from app.models.transaction import Transaction
from app.schemas.document_posting import DocumentPostingCreate, DocumentPostingResponse, DocumentType

# 考虑将这些硬编码的 GUID 移动到配置文件或数据库表中，以提高灵活性
ACCOUNT_GUID_RECEIVABLE = "acc-1100-guid"  # 应收账款
ACCOUNT_GUID_PAYABLE = "acc-payable-guid"  # 应付账款
ACCOUNT_GUID_BANK = "acc-1010-guid"  # 银行存款
ACCOUNT_GUID_REVENUE = "acc-4000-guid"  # 主营业务收入
ACCOUNT_GUID_EXPENSE = "acc-5000-guid"  # 主营业务成本
ACCOUNT_GUID_PROFIT_LOSS = "acc-profit-loss-guid"  # 本年利润


class CRUDDocumentPosting:
    async def post_document(
            self, db: AsyncSession, *, obj_in: DocumentPostingCreate
    ) -> DocumentPostingResponse:
        """
        执行业务单据的过账操作，生成会计凭证和分录。
        这是一个原子操作，如果任何一步失败，整个事务将回滚。
        """
        document_guid = obj_in.document_guid
        document_type = obj_in.document_type

        # 使用更通用的 SQLAlchemyError 捕获所有数据库异常
        try:
            # 1. 根据单据类型获取单据详情，并验证其是否已过账
            crud_obj, db_obj, posting_field_name, description_prefix = await self._get_and_validate_document(
                db, document_guid, document_type
            )

            # 2. 创建会计凭证
            transaction_guid = str(uuid4())
            db_transaction = Transaction(
                guid=transaction_guid,
                description=f"{description_prefix}过账: {db_obj.id or db_obj.bill_number}",
                post_date=db_obj.date_posted or db_obj.bill_date,
                enter_date=db_obj.created_at if hasattr(db_obj, 'created_at') else db_obj.bill_date
            )
            db.add(db_transaction)
            await db.flush()  # 获取 transaction_guid 但不提交

            # 3. 根据单据条目生成分录
            await self._create_splits_from_document(db, db_obj, document_type, transaction_guid)

            # 4. 更新业务单据的过账GUID
            setattr(db_obj, posting_field_name, transaction_guid)
            db.add(db_obj)

            # 5. 提交所有更改
            await db.commit()

            return DocumentPostingResponse(
                success=True,
                message=f"{description_prefix} {db_obj.id or db_obj.bill_number} 过账成功。",
                transaction_guid=transaction_guid,
                document_guid=document_guid,
            )

        except (NotFoundException, ConflictException, BusinessException):
            # 这些是预期的业务异常，直接重新抛出
            await db.rollback()
            raise
        except IntegrityError as e:
            await db.rollback()
            raise ConflictException(detail="过账失败，数据冲突，请检查会计科目或关联数据。") from e
        except SQLAlchemyError as e:
            # 捕获所有其他未预期的数据库错误
            await db.rollback()
            raise BusinessException(detail="过账过程中发生未知数据库错误。") from e
        except Exception as e:
            # 捕获所有其他非数据库错误
            await db.rollback()
            raise BusinessException(detail="过账过程中发生未知错误。") from e

    async def _get_and_validate_document(
        self, db: AsyncSession, document_guid: str, document_type: DocumentType
    ) -> tuple[Union[crud_invoice, crud_purchase_bill], Union[Invoice, PurchaseBill], str, str]:
        """获取并验证业务单据的通用逻辑。"""
        if document_type == DocumentType.INVOICE:
            crud_obj = crud_invoice
            db_obj = await crud_obj.get(db, id=document_guid)
            if not db_obj:
                raise NotFoundException(detail=f"未找到GUID为 {document_guid} 的销售发票。")
            if db_obj.post_txn:
                raise ConflictException(detail="该发票已经过账，不能重复过账。")
            posting_field_name = "post_txn"
            description_prefix = "销售发票"

        elif document_type == DocumentType.PURCHASE_BILL:
            crud_obj = crud_purchase_bill
            db_obj = await crud_obj.get(db, id=document_guid)
            if not db_obj:
                raise NotFoundException(detail=f"未找到GUID为 {document_guid} 的采购账单。")
            if db_obj.post_txn_guid:
                raise ConflictException(detail="该采购账单已经过账，不能重复过账。")
            posting_field_name = "post_txn_guid"
            description_prefix = "采购账单"
        else:
            raise BusinessException(detail=f"不支持的单据类型: {document_type.value}")

        return crud_obj, db_obj, posting_field_name, description_prefix

    async def _create_splits_from_document(
            self, db: AsyncSession, db_obj: Union[Invoice, PurchaseBill], document_type: DocumentType, transaction_guid: str
    ):
        """
        根据业务单据创建会计分录。
        逻辑基于参考数据中的会计准则。
        """
        splits_to_create = []

        if document_type == DocumentType.INVOICE:
            total_amount = sum(entry.price * entry.quantity_num / entry.quantity_denom for entry in db_obj.entries)

            # 借：应收账款
            splits_to_create.append(Split(
                guid=str(uuid4()), txn_guid=transaction_guid, account_guid=ACCOUNT_GUID_RECEIVABLE,
                value=total_amount, quantity_num=1, quantity_denom=1,
                memo=f"销售发票 {db_obj.id} 应收账款",
            ))
            # 贷：主营业务收入
            splits_to_create.append(Split(
                guid=str(uuid4()), txn_guid=transaction_guid, account_guid=ACCOUNT_GUID_REVENUE,
                value=-total_amount, quantity_num=1, quantity_denom=1,
                memo=f"销售发票 {db_obj.id} 收入确认",
            ))

        elif document_type == DocumentType.PURCHASE_BILL:
            # 借：主营业务成本
            splits_to_create.append(Split(
                guid=str(uuid4()), txn_guid=transaction_guid, account_guid=ACCOUNT_GUID_EXPENSE,
                value=db_obj.total_amount, quantity_num=1, quantity_denom=1,
                memo=f"采购账单 {db_obj.bill_number} 成本确认",
            ))
            # 贷：应付账款
            splits_to_create.append(Split(
                guid=str(uuid4()), txn_guid=transaction_guid, account_guid=ACCOUNT_GUID_PAYABLE,
                value=-db_obj.total_amount, quantity_num=1, quantity_denom=1,
                memo=f"对供应商 {db_obj.vendor.name if db_obj.vendor else db_obj.vendor_guid} 的应付账款",
            ))

        if splits_to_create:
            db.add_all(splits_to_create)


# 实例化 CRUD 对象
crud_document_posting = CRUDDocumentPosting()
