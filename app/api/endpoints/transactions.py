from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.logging import logger
from app.models.user import User as UserModel
from app.models.transactions import Transaction as TransactionModel, TransactionType
from app.schemas.transactions import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
    TransactionType as SchemaTransactionType,
)

router = APIRouter()


@router.post("/", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    *,
    db: Session = Depends(get_db),
    transaction_in: TransactionCreate,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Create a new transaction for the current user.
    """
    # Ensure amount sign matches type (optional but good practice)
    if (
        transaction_in.type == SchemaTransactionType.OUTCOME
        and transaction_in.amount > 0
    ):
        transaction_in.amount = -transaction_in.amount
    elif (
        transaction_in.type == SchemaTransactionType.INCOME
        and transaction_in.amount < 0
    ):
        transaction_in.amount = abs(transaction_in.amount)

    # Convert Pydantic enum to string for database
    transaction_data = transaction_in.dict()
    transaction_data["type"] = transaction_in.type.value

    db_transaction = TransactionModel(**transaction_data, user_id=current_user.id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    logger.info(f"User {current_user.id} created transaction {db_transaction.id}")
    return db_transaction


def convert_db_transaction_to_schema(db_transaction):
    """Helper function to convert database transaction to schema with proper enum handling"""
    data = {
        column.name: getattr(db_transaction, column.name)
        for column in db_transaction.__table__.columns
    }

    # Convert string type to enum value
    if data["type"]:
        try:
            data["type"] = SchemaTransactionType(data["type"].lower())
        except ValueError:
            # Default to income if the type is not recognized
            data["type"] = SchemaTransactionType.INCOME

    return data


@router.get("/", response_model=List[Transaction])
def read_transactions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = Query(
        None, description="Filter by transaction type: income or outcome"
    ),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve transactions for the current user.
    Optional filtering by transaction type (income/outcome).
    """
    query = db.query(TransactionModel).filter(
        TransactionModel.user_id == current_user.id
    )

    # Apply type filter if provided
    if type:
        try:
            # Convert string to enum value and then get the string value
            enum_type = SchemaTransactionType(type.lower())
            query = query.filter(TransactionModel.type == enum_type.value)
        except ValueError:
            # If conversion fails, just return all transactions
            logger.warning(f"Invalid transaction type filter: {type}")

    db_transactions = (
        query.order_by(TransactionModel.date.desc()).offset(skip).limit(limit).all()
    )

    # Convert database transactions to schema format with proper enum values
    return [
        convert_db_transaction_to_schema(transaction) for transaction in db_transactions
    ]


@router.get("/{transaction_id}", response_model=Transaction)
def read_transaction(
    *,
    db: Session = Depends(get_db),
    transaction_id: int,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific transaction by ID, owned by the current user.
    """
    transaction = (
        db.query(TransactionModel)
        .filter(
            TransactionModel.id == transaction_id,
            TransactionModel.user_id == current_user.id,
        )
        .first()
    )

    if not transaction:
        logger.warning(
            f"User {current_user.id} tried to access non-existent or unauthorized transaction {transaction_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or not owned by user",
        )

    return convert_db_transaction_to_schema(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    *,
    db: Session = Depends(get_db),
    transaction_id: int,
    current_user: UserModel = Depends(get_current_active_user),
) -> None:
    """
    Delete a transaction owned by the current user.
    """
    transaction = (
        db.query(TransactionModel)
        .filter(
            TransactionModel.id == transaction_id,
            TransactionModel.user_id == current_user.id,
        )
        .first()
    )

    if not transaction:
        logger.warning(
            f"User {current_user.id} tried to delete non-existent or unauthorized transaction {transaction_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or not owned by user",
        )

    db.delete(transaction)
    db.commit()
    logger.info(f"User {current_user.id} deleted transaction {transaction_id}")
    # No content returned on successful delete
