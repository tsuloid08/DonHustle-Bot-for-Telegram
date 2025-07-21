"""
Data models for @donhustle_bot
Dataclass models representing database entities
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Quote:
    """Model for motivational quotes."""
    id: Optional[int]
    quote: str
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class SavedMessage:
    """Model for saved and tagged messages."""
    id: Optional[int]
    chat_id: int
    message_id: int
    content: str
    tag: Optional[str]
    saved_by: int
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Reminder:
    """Model for scheduled reminders."""
    id: Optional[int]
    chat_id: int
    user_id: int
    message: str
    remind_time: datetime
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class UserActivity:
    """Model for tracking user activity."""
    user_id: int
    chat_id: int
    last_activity: Optional[datetime] = None
    message_count: int = 0
    
    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.now()


@dataclass
class CustomCommand:
    """Model for custom bot commands."""
    id: Optional[int]
    chat_id: int
    command_name: str
    response: str
    created_by: int
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Config:
    """Model for bot configuration settings."""
    chat_id: int
    key: str
    value: str


@dataclass
class SpamFilter:
    """Model for spam filter words."""
    id: Optional[int]
    chat_id: int
    filter_word: str
    action: str = 'warn'
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()