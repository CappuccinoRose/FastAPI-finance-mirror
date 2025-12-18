from typing import Optional
from pydantic import BaseModel, Field

class EmployeeBase(BaseModel):
    username: str = Field(..., max_length=255)
    language: Optional[str] = Field(None, max_length=10)
    active: bool = True

class EmployeeCreate(EmployeeBase):
    password: str = Field(..., max_length=255)
    id: Optional[str] = Field(None, max_length=50)

class EmployeeUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=255)
    language: Optional[str] = Field(None, max_length=10)
    active: Optional[bool] = None
    password: Optional[str] = Field(None, max_length=255)
    id: Optional[str] = Field(None, max_length=50)

class Employee(EmployeeBase):
    guid: str
    id: Optional[str] = None
    hashed_password: str

    class Config:
        from_attributes = True
