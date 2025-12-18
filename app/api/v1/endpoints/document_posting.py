# finance_mirror_backend/app/api/v1/endpoints/document_posting.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user
from app.crud import crud_document_posting
from app.schemas.document_posting import DocumentPostingCreate, DocumentPostingResponse
from app.schemas.user import UserWithAuth

router = APIRouter()

@router.post("/", response_model=DocumentPostingResponse, summary="业务单据过账")
async def post_document(
    *,
    db: AsyncSession = Depends(get_db),
    obj_in: DocumentPostingCreate,
    current_user: UserWithAuth = Depends(get_current_active_user)
):
    """
    对指定的业务单据（如销售发票、采购账单）执行过账操作，生成会计凭证和分录。
    - **document_type**: 单据类型，支持 'invoice' (销售发票) 或 'purchase_bill' (采购账单)。
    - **document_guid**: 要过账的单据的唯一标识符 (GUID)。
    """
    result = await crud_document_posting.post_document(db=db, obj_in=obj_in)
    return result

