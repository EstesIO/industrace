# backend/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid
from typing import Optional
from .role import RoleRead


class UserCreate(BaseModel):
    name: str = Field(..., max_length=255, description="User name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=255, description="Password")
    role_id: uuid.UUID
    is_active: Optional[bool] = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    name: str
    role_id: Optional[uuid.UUID] = None
    role: Optional[RoleRead] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
