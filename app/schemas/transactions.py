# app/schemas/transactions.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# Shared properties
class TransactionBase(BaseModel):
    name: str = Field(..., max_length=100)
    amount: (
        float  # Using float for simplicity, consider Decimal for financial precision
    )
    type: str = Field(..., max_length=50)  # e.g., "income", "expense"
    category: str = Field(..., max_length=50)  # e.g., "groceries", "salary"
    date: datetime


# Properties to receive via API on creation
class TransactionCreate(TransactionBase):
    pass  # All fields from Base are required for creation


# Properties to receive via API on update, all optional
class TransactionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    amount: Optional[float] = None
    type: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    date: Optional[datetime] = None


# Properties shared by models stored in DB
class TransactionInDBBase(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = (
        None  # Make updated_at optional as it might be null initially
    )

    class Config:
        orm_mode = True  # Use orm_mode instead of from_attributes in Pydantic v1


# Properties to return to client
class Transaction(TransactionInDBBase):
    pass


# Properties stored in DB
class TransactionInDB(TransactionInDBBase):
    pass
