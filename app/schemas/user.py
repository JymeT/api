from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: str = Field(..., regex=r"^\+?[0-9]{10,15}$", examples="01210457898")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(
        None, regex=r"^\+?[0-9]{10,15}$", examples="01210457898"
    )
    password: Optional[str] = Field(None, min_length=8)


class UserInDBBase(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str
