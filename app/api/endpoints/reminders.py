from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.reminder import Reminder, ReminderCreate, ReminderUpdate
from app.db.session import get_db
from app.models.reminders import Reminder as ReminderModel
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=Reminder, status_code=status.HTTP_201_CREATED)
def create_reminder(
    reminder_in: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Create the reminder using current user's ID
    db_reminder = ReminderModel(**reminder_in.dict(), user_id=current_user.id)
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder


@router.get("/", response_model=List[Reminder])
def read_reminders(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Only return reminders for the current user
    reminders = (
        db.query(ReminderModel)
        .filter(ReminderModel.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return reminders


@router.get("/{reminder_id}", response_model=Reminder)
def read_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    reminder = (
        db.query(ReminderModel)
        .filter(
            ReminderModel.id == reminder_id, ReminderModel.user_id == current_user.id
        )
        .first()
    )
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )
    return reminder


@router.put("/{reminder_id}", response_model=Reminder)
def update_reminder(
    reminder_id: int,
    reminder_in: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_reminder = (
        db.query(ReminderModel)
        .filter(
            ReminderModel.id == reminder_id, ReminderModel.user_id == current_user.id
        )
        .first()
    )
    if not db_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )

    update_data = reminder_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_reminder, key, value)

    db.commit()
    db.refresh(db_reminder)
    return db_reminder


@router.delete("/{reminder_id}", response_model=Reminder)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_reminder = (
        db.query(ReminderModel)
        .filter(
            ReminderModel.id == reminder_id, ReminderModel.user_id == current_user.id
        )
        .first()
    )
    if not db_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )

    db.delete(db_reminder)
    db.commit()
    return db_reminder
