from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.logging import logger
from app.models.user import User as UserModel
from app.models.transactions import Transaction as TransactionModel
from app.schemas.transactions import Transaction, TransactionCreate, TransactionUpdate

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
    if transaction_in.type.lower() == "expense" and transaction_in.amount > 0:
        transaction_in.amount = -transaction_in.amount
    elif transaction_in.type.lower() == "income" and transaction_in.amount < 0:
        transaction_in.amount = abs(transaction_in.amount)

    db_transaction = TransactionModel(**transaction_in.dict(), user_id=current_user.id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    logger.info(f"User {current_user.id} created transaction {db_transaction.id}")
    return db_transaction


@router.get("/", response_model=List[Transaction])
def read_transactions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve transactions for the current user.
    """
    transactions = (
        db.query(TransactionModel)
        .filter(TransactionModel.user_id == current_user.id)
        .order_by(TransactionModel.date.desc())  # Optional: order by date
        .offset(skip)
        .limit(limit)
        .all()
    )
    return transactions


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
    return transaction


# @router.put("/{transaction_id}", response_model=Transaction)
# def update_transaction(
#     *,
#     db: Session = Depends(get_db),
#     transaction_id: int,
#     transaction_in: TransactionUpdate,
#     current_user: UserModel = Depends(get_current_active_user),
# ) -> Any:
#     """
#     Update a transaction owned by the current user.
#     """
#     transaction = (
#         db.query(TransactionModel)
#         .filter(
#             TransactionModel.id == transaction_id,
#             TransactionModel.user_id == current_user.id,
#         )
#         .first()
#     )

#     if not transaction:
#         logger.warning(
#             f"User {current_user.id} tried to update non-existent or unauthorized transaction {transaction_id}"
#         )
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Transaction not found or not owned by user",
#         )

#     update_data = transaction_in.dict(exclude_unset=True)

#     # Optional: Adjust amount sign if type is also updated
#     if "type" in update_data and "amount" in update_data:
#         if update_data["type"].lower() == "expense" and update_data["amount"] > 0:
#             update_data["amount"] = -update_data["amount"]
#         elif update_data["type"].lower() == "income" and update_data["amount"] < 0:
#             update_data["amount"] = abs(update_data["amount"])
#     elif (
#         "amount" in update_data
#         and transaction.type.lower() == "expense"
#         and update_data["amount"] > 0
#     ):
#         update_data["amount"] = -update_data["amount"]
#     elif (
#         "amount" in update_data
#         and transaction.type.lower() == "income"
#         and update_data["amount"] < 0
#     ):
#         update_data["amount"] = abs(update_data["amount"])

#     for field, value in update_data.items():
#         setattr(transaction, field, value)

#     db.add(transaction)
#     db.commit()
#     db.refresh(transaction)
#     logger.info(f"User {current_user.id} updated transaction {transaction.id}")
#     return transaction


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
