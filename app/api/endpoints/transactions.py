from typing import Any, List, Optional, Dict
from sqlalchemy import func, extract
from datetime import datetime
import calendar

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
    query = (
        db.query(TransactionModel)
        .filter(TransactionModel.user_id == current_user.id)
        .order_by(TransactionModel.date.desc())
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


@router.get("/dashboard/categories", response_model=Dict[str, float])
def get_transaction_categories_breakdown(
    *,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Get breakdown of transaction categories for pie chart visualization.
    Returns the proportion of spending in each category.
    """
    # Add debug logging
    logger.info(f"Starting category breakdown calculation for user {current_user.id}")

    # Get all outcome transactions for this user
    transactions = (
        db.query(
            TransactionModel.category, func.sum(TransactionModel.amount).label("total")
        )
        .filter(
            TransactionModel.user_id == current_user.id,
            TransactionModel.type == "outcome",
        )
        .group_by(TransactionModel.category)
        .all()
    )

    # Debug log the found transactions
    logger.info(f"Found {len(transactions)} category groups for user {current_user.id}")
    for t in transactions:
        logger.info(f"Category: {t.category}, Total: {t.total}")

    # Calculate total spending (as absolute value since outcome amounts are negative)
    total_spending = sum(abs(t.total) for t in transactions) if transactions else 0
    logger.info(f"Total spending: {total_spending}")

    # If no transactions found, return empty dict
    if not transactions:
        logger.info(f"No outcome transactions found for user {current_user.id}")
        return {}

    # Even if total spending is 0, return the categories with equal proportions
    if total_spending == 0:
        logger.info(
            f"Total spending is zero, returning equal proportions for all categories"
        )
        equal_proportion = round(1.0 / len(transactions), 2) if transactions else 0
        result = {t.category: equal_proportion for t in transactions}
        logger.info(f"Generated equal proportions: {result}")
        return result

    # Calculate proportion of spending for each category
    result = {t.category: round(abs(t.total) / total_spending, 2) for t in transactions}

    logger.info(f"Generated category breakdown: {result}")
    return result


@router.get("/dashboard/monthly-spending", response_model=Dict[str, float])
def get_monthly_spending(
    *,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    year: Optional[int] = Query(
        None, description="Filter by year (defaults to current year)"
    ),
) -> Any:
    """
    Get monthly outcome totals for the current user.
    Returns a dictionary with months as keys and total spending as values.
    """
    # Default to current year if not specified
    if not year:
        year = datetime.now().year

    logger.info(f"Getting monthly spending for user {current_user.id} for year {year}")

    # Query to get monthly totals of outcome transactions
    monthly_totals = (
        db.query(
            extract("month", TransactionModel.date).label("month"),
            func.sum(TransactionModel.amount).label("total"),
        )
        .filter(
            TransactionModel.user_id == current_user.id,
            TransactionModel.type == "outcome",
            extract("year", TransactionModel.date) == year,
        )
        .group_by(extract("month", TransactionModel.date))
        .all()
    )

    logger.info(f"Found {len(monthly_totals)} months with outcome transactions")

    # Create a dictionary with all months initialized to 0
    result = {month: 0.0 for month in range(1, 13)}

    # Fill in the actual totals (as absolute values since outcome transactions are negative)
    for item in monthly_totals:
        month_num = int(item.month)
        # Convert to absolute value since outcome transactions are negative
        result[month_num] = abs(float(item.total))

    # For better readability, convert month numbers to month names
    named_result = {
        calendar.month_name[month]: amount for month, amount in result.items()
    }

    logger.info(f"Monthly spending data generated: {named_result}")
    return named_result


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
