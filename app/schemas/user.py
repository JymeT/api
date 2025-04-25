from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: str

    @validator('phone')
    def phone_validation(cls, v):
        # Simple phone validation - can be enhanced based on your requirements
        if not re.match(r'^\+?[0-9]{10,15}$', v):
            raise ValueError('Invalid phone number format')
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)

    @validator('phone')
    def phone_validation(cls, v):
        if v is None:
            return v
        if not re.match(r'^\+?[0-9]{10,15}$', v):
            raise ValueError('Invalid phone number format')
        return v


class UserInDBBase(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str 