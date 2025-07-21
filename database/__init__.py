# Database package for data persistence and management

from .manager import DatabaseManager, get_database_manager, close_database
from .models import Quote, SavedMessage, Reminder, UserActivity, CustomCommand, Config, SpamFilter
from .repositories import (
    QuoteRepository, MessageRepository, ReminderRepository, 
    ConfigRepository, UserActivityRepository, CustomCommandRepository, SpamFilterRepository
)

__all__ = [
    'DatabaseManager', 'get_database_manager', 'close_database',
    'Quote', 'SavedMessage', 'Reminder', 'UserActivity', 'CustomCommand', 'Config', 'SpamFilter',
    'QuoteRepository', 'MessageRepository', 'ReminderRepository', 
    'ConfigRepository', 'UserActivityRepository', 'CustomCommandRepository', 'SpamFilterRepository'
]