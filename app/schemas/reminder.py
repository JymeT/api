from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# Shared properties
class ReminderBase(BaseModel):
    name: str = Field(..., max_length=100)
    active: bool = True
    next_date: datetime
    category: str = Field(..., max_length=50)
    amount: int
    frequency: int  # Frequency in days
    description: Optional[str] = Field(None, max_length=255)


# Properties to receive via API on creation
class ReminderCreate(ReminderBase):
    pass


# Properties to receive via API on update, all optional
class ReminderUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None
    next_date: Optional[datetime] = None
    frequency: Optional[int] = None
    description: Optional[str] = Field(None, max_length=255)
    amount: Optional[int] = None


# Properties shared by models stored in DB
class ReminderInDBBase(ReminderBase):
    id: int
    user_id: int  # Foreign key to user, keeping it in DB model
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Properties to return to client
class Reminder(ReminderInDBBase):
    # Hide user_id from client
    class Config:
        orm_mode = True
        exclude = {"user_id"}


# Properties stored in DB
class ReminderInDB(ReminderInDBBase):
    pass
