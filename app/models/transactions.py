from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import DateTime
import enum

from app.db.session import Base


class TransactionType(str, enum.Enum):
    INCOME = "income"
    OUTCOME = "outcome"


class Transaction(Base):
    __tablename__ = "Transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    name = Column(String, index=True)
    amount = Column(Integer, nullable=False)
    type = Column(
        String, nullable=False
    )  # Keep as String to be compatible with existing data
    category = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
