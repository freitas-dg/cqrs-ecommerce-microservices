from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=['Douglas Freitas'])
    cpf: str = Field(..., min_length=11, max_length=14, examples=['52998224725'])
    email: EmailStr = Field(..., examples=['douglas@example.com'])
    phone_number: str = Field(..., min_length=8, max_length=20, examples=['+5511999998888'])

class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=8, max_length=20)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    cpf: str
    email: str
    phone_number: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
