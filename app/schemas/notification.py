from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class NotificationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REFUSED = "refused"
    EXTENDED = "extended"


class NotificationBase(BaseModel):
    name: str
    reminder_id: int
    date: Optional[datetime] = None


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    status: NotificationStatus


class NotificationResponse(NotificationBase):
    id: int
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
