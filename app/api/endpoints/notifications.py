from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.notification import Notification
from app.models.transactions import Transaction, TransactionType
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
    NotificationUpdate,
)

router = APIRouter()


@router.post(
    "/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED
)
def add_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new notification for the current user.
    """
    db_notification = Notification(
        user_id=current_user.id,
        reminder_id=notification.reminder_id,
        name=notification.name,
        date=notification.date or datetime.now(),
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


@router.get("/", response_model=List[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all notifications for the current user.
    """
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return notifications


@router.put("/{notification_id}", response_model=NotificationResponse)
def notification_actions(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process notification actions:
    - ACCEPTED: Remove notification, add new transaction record, update reminder date by frequency
    - REFUSED: Remove notification, update reminder date by frequency
    - EXTENDED: Update the notification by one day
    """
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    # Get the reminder associated with this notification
    reminder = notification.reminder
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No reminder associated with this notification",
        )

    # Store notification data before potential deletion for the response
    notification_data = NotificationResponse.model_validate(notification.__dict__)

    # Handle different status updates
    if notification_update.status == NotificationStatus.ACCEPTED:
        # Create a new transaction record
        new_transaction = Transaction(
            user_id=current_user.id,
            name=f"Payment for {notification.name}",
            amount=reminder.amount,
            type=TransactionType.OUTCOME,
            category="Reminder Payment",
        )
        db.add(new_transaction)

        # Update the reminder date by the frequency
        reminder.next_date = reminder.next_date + timedelta(days=reminder.frequency)
        db.add(reminder)

        # Remove the notification
        db.delete(notification)
        db.commit()

        # Return the notification data that was deleted
        return notification_data

    elif notification_update.status == NotificationStatus.REFUSED:
        # Update the reminder date by the frequency
        reminder.next_date = reminder.next_date + timedelta(days=reminder.frequency)
        db.add(reminder)

        # Remove the notification
        db.delete(notification)
        db.commit()

        # Return the notification data that was deleted
        return notification_data

    elif notification_update.status == NotificationStatus.EXTENDED:
        # Update the notification date by one day
        notification.date = notification.date + timedelta(days=1)
        notification.updated_at = datetime.now()
        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    # If we reach here, update the notification status
    notification.updated_at = datetime.now()
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification
