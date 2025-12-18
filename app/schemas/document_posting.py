# finance_mirror_backend/app/schemas/document_posting.py

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# 使用枚举来限制单据类型，增加健壮性
class DocumentType(str, Enum):
    invoice = "invoice"
    purchase_bill = "purchase_bill"


class DocumentPostingBase(BaseModel):
    """
    业务单据过账请求的基础模型
    """
    document_type: DocumentType = Field(..., description="单据类型，如 'invoice' 或 'purchase_bill'")
    document_guid: str = Field(..., description="要过账的单据的唯一标识符 (GUID)")


class DocumentPostingCreate(DocumentPostingBase):
    """
    用于创建过账请求的模型
    """
    pass


class DocumentPostingResponse(BaseModel):
    """
    用于返回过账操作结果的模型
    """
    success: bool = Field(..., description="过账操作是否成功")
    message: str = Field(..., description="操作结果信息")
    transaction_guid: Optional[str] = Field(None, description="生成的会计凭证的GUID")
    document_guid: str = Field(..., description="原业务单据的GUID")

    class Config:
        from_attributes = True

