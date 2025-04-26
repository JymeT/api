# Import all the models here so that Alembic can discover them
from app.db.session import Base
from app.models.user import User
from app.models.transactions import Transaction
from app.models.reminders import Reminder
