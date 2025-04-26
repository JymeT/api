from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from pydantic import BaseModel
import string

from app.api.deps import get_current_active_user, get_db
from app.core.security import get_password_hash
from app.core.logging import logger
from app.models.user import User
from app.models.transactions import Transaction, TransactionType
from app.models.reminders import Reminder
from app.models.notification import Notification

router = APIRouter()

# Request model for dummy data generation
class DummyDataParams(BaseModel):
    num_users: int = 5
    num_transactions_per_user: int = 20
    num_reminders_per_user: int = 3
    num_notifications_per_reminder: int = 2
    clear_existing: bool = False

# Categories for transactions
INCOME_CATEGORIES = ["Salary", "Freelance", "Gift", "Investment", "Bonus"]
OUTCOME_CATEGORIES = ["Food", "Housing", "Transportation", "Entertainment", "Healthcare", "Shopping", "Utilities", "Education", "Travel", "Other"]

# Names for dummy data
FIRST_NAMES = ["John", "Jane", "Mike", "Sarah", "Alex", "Emily", "David", "Lisa", "Robert", "Jennifer"]
LAST_NAMES = ["Smith", "Johnson", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Wilson"]

@router.post("/generate", response_model=Dict[str, Any])
def generate_dummy_data(
    params: DummyDataParams,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Generate dummy data for all models.
    This endpoint is accessible to any authenticated user.
    """
    # Clear existing data if requested
    if params.clear_existing:
        logger.info("Clearing existing data before generating dummy data")
        db.query(Notification).filter(Notification.user_id == current_user.id).delete()
        db.query(Reminder).filter(Reminder.user_id == current_user.id).delete()
        db.query(Transaction).filter(Transaction.user_id == current_user.id).delete()
        db.commit()

    # Generate transactions for the current user
    total_transactions = 0
    today = datetime.now()
    
    # Create transactions spanning the last 12 months
    for j in range(params.num_transactions_per_user):
        # Random date within the last year
        random_days = random.randint(0, 365)
        transaction_date = today - timedelta(days=random_days)
        
        # Randomly decide if this is income or outcome
        is_income = random.random() < 0.3  # 30% income, 70% outcome
        
        if is_income:
            transaction_type = TransactionType.INCOME.value
            amount = random.randint(1000, 5000)  # Income is positive
            category = random.choice(INCOME_CATEGORIES)
            name = f"{category} payment"
        else:
            transaction_type = TransactionType.OUTCOME.value
            amount = -random.randint(50, 1000)  # Outcome is negative
            category = random.choice(OUTCOME_CATEGORIES)
            name = f"{category} expense"
        
        transaction = Transaction(
            user_id=current_user.id,
            name=name,
            amount=amount,
            type=transaction_type,
            category=category,
            date=transaction_date
        )
        
        db.add(transaction)
        total_transactions += 1
    
    # Generate reminders for the current user
    total_reminders = 0
    reminders = []
    for k in range(params.num_reminders_per_user):
        # Set next date within the next month
        next_date = datetime.now() + timedelta(days=random.randint(1, 30))
        
        # Create reminder
        category = random.choice(OUTCOME_CATEGORIES)
        amount = -random.randint(50, 500)  # Negative for payments
        
        reminder = Reminder(
            name=f"{category} payment",
            user_id=current_user.id,
            active=True,
            next_date=next_date,
            category=category,
            amount=amount,
            frequency=random.choice([7, 14, 30, 90]),  # Weekly, bi-weekly, monthly, quarterly
            description=f"Reminder for {category.lower()} payment"
        )
        
        db.add(reminder)
        db.flush()  # Flush to get reminder ID
        reminders.append(reminder)
        total_reminders += 1
    
    # Generate notifications for reminders
    total_notifications = 0
    for reminder in reminders:
        for m in range(params.num_notifications_per_reminder):
            # Create a notification date (past or future)
            notification_date = reminder.next_date - timedelta(days=random.randint(0, 7))
            
            notification = Notification(
                reminder_id=reminder.id,
                user_id=current_user.id,
                date=notification_date,
                name=f"Reminder: {reminder.name}"
            )
            
            db.add(notification)
            total_notifications += 1
    
    # Commit all changes
    db.commit()
    
    logger.info(f"Generated dummy data for user {current_user.id}: {total_transactions} transactions, {total_reminders} reminders, {total_notifications} notifications")
    
    return {
        "transactions_created": total_transactions,
        "reminders_created": total_reminders,
        "notifications_created": total_notifications
    }