# app/schemas/period_closing.py

import json
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.transaction import Transaction

# --- 辅助函数和常量 ---
# 用于在 transaction.description 中存储结转任务信息
CLOSING_DESCRIPTION_PREFIX = "[SYSTEM_CLOSING]"


def _parse_closing_description(description: str) -> dict:
    """
    从结转凭证的 description 中解析出任务元数据。
    格式示例: "[SYSTEM_CLOSING] {\"type\": \"income_expense\", \"period\": \"2023-12-31\", \"status\": \"completed\"}"
    """
    if not description or not description.startswith(CLOSING_DESCRIPTION_PREFIX):
        return {}
    try:
        json_str = description[len(CLOSING_DESCRIPTION_PREFIX):].strip()
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        # 如果解析失败，返回空字典，避免程序崩溃
        return {}


def _build_closing_description(closing_type: str, period_end_date: date, status: str) -> str:
    """
    构建用于存储结转任务元数据的 description 字符串。
    """
    metadata = {
        "type": closing_type,
        "period": period_end_date.isoformat(),
        "status": status
    }
    return f"{CLOSING_DESCRIPTION_PREFIX} {json.dumps(metadata)}"


# --- Pydantic Schemas ---

class PeriodClosingBase(BaseModel):
    """期末结转任务的基类，包含公共字段"""
    closing_type: str = Field(..., description="结转类型，如 'income_expense'")
    period_end_date: date = Field(..., description="结转的会计期间截止日期")

    @field_validator('closing_type')
    @classmethod
    def validate_closing_type(cls, v):
        # 这里可以定义允许的结转类型
        allowed_types = ["income_expense", "depreciation"]  # 未来可扩展
        if v not in allowed_types:
            raise ValueError(f"结转类型必须是以下之一: {', '.join(allowed_types)}")
        return v


class PeriodClosingCreate(PeriodClosingBase):
    """用于发起期末结转任务的请求 Schema"""
    pass


class PeriodClosingUpdate(BaseModel):
    """用于内部更新结转任务状态的 Schema，API 不直接暴露"""
    status: str = Field(..., description="任务状态，如 'pending', 'in_progress', 'completed', 'failed'")
    transaction_guid: Optional[str] = Field(None, description="关联的最终凭证GUID")
    error_message: Optional[str] = Field(None, description="失败时的错误信息")


class PeriodClosing(Transaction):
    """
    用于响应的期末结转任务 Schema。
    它继承自 Transaction，因为它本质上就是一笔凭证，
    但额外提供了从 description 解析出的任务信息。
    """
    # 从 Transaction 继承的字段: guid, post_date, enter_date, description, splits
    # 新增字段，用于前端直接使用
    closing_type: Optional[str] = None
    period_end_date: Optional[date] = None
    status: Optional[str] = None
    error_message: Optional[str] = None

    # 用于标识这是一个结转任务，而不是普通凭证
    is_system_closing: bool = False

    @field_validator('is_system_closing', mode='before')
    @classmethod
    def check_if_system_closing(cls, v, values):
        """检查 description 是否以系统前缀开头，以设置 is_system_closing 标志"""
        description = values.get('description')
        if description and description.startswith(CLOSING_DESCRIPTION_PREFIX):
            return True
        return False

    @field_validator('closing_type', 'period_end_date', 'status', 'error_message', mode='before')
    @classmethod
    def parse_description_fields(cls, v, values):
        """
        这个验证器会在所有字段之后运行。
        它会从 description 中解析出所有元数据，并填充到对应的字段中。
        """
        description = values.get('description')
        if description and description.startswith(CLOSING_DESCRIPTION_PREFIX):
            parsed_data = _parse_closing_description(description)
            # 根据当前正在验证的字段名，从解析数据中返回对应的值
            # Pydantic 会为每个字段调用此验证器
            field_name = cls.__name__  # 获取当前正在验证的字段名，这需要一点技巧
            # 一个更简单的方式是直接在模型初始化后处理，或者使用 root_validator
            # 为了清晰，我们换一种方式：使用 model_validator
            return None  # 这里先返回 None，让 model_validator 处理
        return v

    # 使用 Pydantic V2 的新模型验证器，更清晰
    from pydantic import model_validator

    @model_validator(mode='before')
    @classmethod
    def populate_fields_from_description(cls, data):
        """
        在模型创建前，从 description 中提取数据并填充到模型字段。
        """
        if isinstance(data, dict):
            description = data.get('description')
            if description and isinstance(description, str) and description.startswith(CLOSING_DESCRIPTION_PREFIX):
                parsed_data = _parse_closing_description(description)
                data.update(parsed_data)  # 将解析出的数据合并到模型数据中
                data['is_system_closing'] = True
            else:
                data['is_system_closing'] = False
        return data

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }

