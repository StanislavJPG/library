import uuid
from typing import Optional

from fastapi_users import schemas
from pydantic import EmailStr, Field


class UserRead(schemas.BaseUser[uuid.UUID]):
    id: uuid.UUID
    username: str
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False


class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    username: str = Field(min_length=3)
    password: str = Field(min_length=7)
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False


class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str]
