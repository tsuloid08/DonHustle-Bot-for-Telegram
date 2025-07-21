"""
Repository classes for @donhustle_bot
Provides CRUD operations for all database entities
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
import logging

from .manager import DatabaseManager
from .models import Quote, SavedMessage, Reminder, UserActivity, CustomCommand, Config, SpamFilter


class BaseRepository:
    """Base repository class with common database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)


class QuoteRepository(BaseRepository):
    """Repository for managing motivational quotes."""
    
    def add_quote(self, quote: str) -> int:
        """
        Add a new quote to the database.
        
        Args:
            quote: The quote text
            
        Returns:
            ID of the inserted quote
        """
        query = "INSERT INTO quotes (quote) VALUES (?)"
        return self.db.execute_insert(query, (quote,))
    
    def get_all_quotes(self) -> List[Quote]:
        """
        Get all quotes from the database.
        
        Returns:
            List of Quote objects
        """
        query = "SELECT id, quote, created_at FROM quotes ORDER BY id DESC"
        rows = self.db.execute_query(query)
        
        return [
            Quote(
                id=row['id'],
                quote=row['quote'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]
    
    def get_quote_by_id(self, quote_id: int) -> Optional[Quote]:
        """
        Get a specific quote by ID.
        
        Args:
            quote_id: The quote ID
            
        Returns:
            Quote object or None if not found
        """
        query = "SELECT id, quote, created_at FROM quotes WHERE id = ?"
        rows = self.db.execute_query(query, (quote_id,))
        
        if not rows:
            return None
        
        row = rows[0]
        return Quote(
            id=row['id'],
            quote=row['quote'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    def delete_quote(self, quote_id: int) -> bool:
        """
        Delete a quote by ID.
        
        Args:
            quote_id: The quote ID to delete
            
        Returns:
            True if quote was deleted, False otherwise
        """
        query = "DELETE FROM quotes WHERE id = ?"
        affected_rows = self.db.execute_update(query, (quote_id,))
        return affected_rows > 0
    
    def clear_all_quotes(self) -> int:
        """
        Delete all quotes from the database.
        
        Returns:
            Number of deleted quotes
        """
        query = "DELETE FROM quotes"
        return self.db.execute_update(query)
    
    def get_random_quote(self) -> Optional[Quote]:
        """
        Get a random quote from the database.
        
        Returns:
            Random Quote object or None if no quotes exist
        """
        query = "SELECT id, quote, created_at FROM quotes ORDER BY RANDOM() LIMIT 1"
        rows = self.db.execute_query(query)
        
        if not rows:
            return None
        
        row = rows[0]
        return Quote(
            id=row['id'],
            quote=row['quote'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )


class MessageRepository(BaseRepository):
    """Repository for managing saved messages."""
    
    def save_message(self, chat_id: int, message_id: int, content: str, 
                    saved_by: int, tag: Optional[str] = None) -> int:
        """
        Save a message to the database.
        
        Args:
            chat_id: Chat ID where message was sent
            message_id: Telegram message ID
            content: Message content
            saved_by: User ID who saved the message
            tag: Optional tag for the message
            
        Returns:
            ID of the saved message
        """
        query = """
            INSERT INTO saved_messages (chat_id, message_id, content, saved_by, tag)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (chat_id, message_id, content, saved_by, tag))
    
    def get_saved_messages(self, chat_id: int) -> List[SavedMessage]:
        """
        Get all saved messages for a chat.
        
        Args:
            chat_id: Chat ID to get messages for
            
        Returns:
            List of SavedMessage objects
        """
        query = """
            SELECT id, chat_id, message_id, content, tag, saved_by, created_at
            FROM saved_messages
            WHERE chat_id = ?
            ORDER BY id DESC
        """
        rows = self.db.execute_query(query, (chat_id,))
        
        return [
            SavedMessage(
                id=row['id'],
                chat_id=row['chat_id'],
                message_id=row['message_id'],
                content=row['content'],
                tag=row['tag'],
                saved_by=row['saved_by'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]
    
    def get_messages_by_tag(self, chat_id: int, tag: str) -> List[SavedMessage]:
        """
        Get saved messages by tag.
        
        Args:
            chat_id: Chat ID to search in
            tag: Tag to search for
            
        Returns:
            List of SavedMessage objects with the specified tag
        """
        query = """
            SELECT id, chat_id, message_id, content, tag, saved_by, created_at
            FROM saved_messages
            WHERE chat_id = ? AND tag = ?
            ORDER BY id DESC
        """
        rows = self.db.execute_query(query, (chat_id, tag))
        
        return [
            SavedMessage(
                id=row['id'],
                chat_id=row['chat_id'],
                message_id=row['message_id'],
                content=row['content'],
                tag=row['tag'],
                saved_by=row['saved_by'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]


class ReminderRepository(BaseRepository):
    """Repository for managing reminders."""
    
    def create_reminder(self, chat_id: int, user_id: int, message: str,
                       remind_time: datetime, is_recurring: bool = False,
                       recurrence_pattern: Optional[str] = None) -> int:
        """
        Create a new reminder.
        
        Args:
            chat_id: Chat ID for the reminder
            user_id: User ID who created the reminder
            message: Reminder message
            remind_time: When to send the reminder
            is_recurring: Whether the reminder repeats
            recurrence_pattern: Pattern for recurring reminders
            
        Returns:
            ID of the created reminder
        """
        query = """
            INSERT INTO reminders (chat_id, user_id, message, remind_time, is_recurring, recurrence_pattern)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (
            chat_id, user_id, message, remind_time.isoformat(),
            is_recurring, recurrence_pattern
        ))
    
    def get_active_reminders(self, chat_id: int) -> List[Reminder]:
        """
        Get all active reminders for a chat.
        
        Args:
            chat_id: Chat ID to get reminders for
            
        Returns:
            List of active Reminder objects
        """
        query = """
            SELECT id, chat_id, user_id, message, remind_time, is_recurring, 
                   recurrence_pattern, is_active, created_at
            FROM reminders
            WHERE chat_id = ? AND is_active = TRUE
            ORDER BY remind_time ASC
        """
        rows = self.db.execute_query(query, (chat_id,))
        
        return [
            Reminder(
                id=row['id'],
                chat_id=row['chat_id'],
                user_id=row['user_id'],
                message=row['message'],
                remind_time=datetime.fromisoformat(row['remind_time']),
                is_recurring=bool(row['is_recurring']),
                recurrence_pattern=row['recurrence_pattern'],
                is_active=bool(row['is_active']),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]
    
    def get_due_reminders(self, current_time: datetime) -> List[Reminder]:
        """
        Get all reminders that are due to be sent.
        
        Args:
            current_time: Current datetime to check against
            
        Returns:
            List of due Reminder objects
        """
        query = """
            SELECT id, chat_id, user_id, message, remind_time, is_recurring,
                   recurrence_pattern, is_active, created_at
            FROM reminders
            WHERE remind_time <= ? AND is_active = TRUE
            ORDER BY remind_time ASC
        """
        rows = self.db.execute_query(query, (current_time.isoformat(),))
        
        return [
            Reminder(
                id=row['id'],
                chat_id=row['chat_id'],
                user_id=row['user_id'],
                message=row['message'],
                remind_time=datetime.fromisoformat(row['remind_time']),
                is_recurring=bool(row['is_recurring']),
                recurrence_pattern=row['recurrence_pattern'],
                is_active=bool(row['is_active']),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]
    
    def deactivate_reminder(self, reminder_id: int) -> bool:
        """
        Deactivate a reminder (for one-time reminders).
        
        Args:
            reminder_id: ID of the reminder to deactivate
            
        Returns:
            True if reminder was deactivated, False otherwise
        """
        query = "UPDATE reminders SET is_active = FALSE WHERE id = ?"
        affected_rows = self.db.execute_update(query, (reminder_id,))
        return affected_rows > 0


class ConfigRepository(BaseRepository):
    """Repository for managing bot configuration."""
    
    def set_config(self, chat_id: int, key: str, value: str) -> None:
        """
        Set a configuration value for a chat.
        
        Args:
            chat_id: Chat ID
            key: Configuration key
            value: Configuration value
        """
        query = """
            INSERT OR REPLACE INTO config (chat_id, key, value)
            VALUES (?, ?, ?)
        """
        self.db.execute_update(query, (chat_id, key, value))
    
    def get_config(self, chat_id: int, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value for a chat.
        
        Args:
            chat_id: Chat ID
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        query = "SELECT value FROM config WHERE chat_id = ? AND key = ?"
        rows = self.db.execute_query(query, (chat_id, key))
        
        if rows:
            return rows[0]['value']
        return default
    
    def get_all_config(self, chat_id: int) -> Dict[str, str]:
        """
        Get all configuration values for a chat.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Dictionary of configuration key-value pairs
        """
        query = "SELECT key, value FROM config WHERE chat_id = ?"
        rows = self.db.execute_query(query, (chat_id,))
        
        return {row['key']: row['value'] for row in rows}
    
    def delete_config(self, chat_id: int, key: str) -> bool:
        """
        Delete a configuration value.
        
        Args:
            chat_id: Chat ID
            key: Configuration key to delete
            
        Returns:
            True if config was deleted, False otherwise
        """
        query = "DELETE FROM config WHERE chat_id = ? AND key = ?"
        affected_rows = self.db.execute_update(query, (chat_id, key))
        return affected_rows > 0


class UserActivityRepository(BaseRepository):
    """Repository for managing user activity tracking."""
    
    def update_user_activity(self, user_id: int, chat_id: int) -> None:
        """
        Update user activity timestamp and increment message count.
        
        Args:
            user_id: User ID
            chat_id: Chat ID
        """
        query = """
            INSERT OR REPLACE INTO user_activity (user_id, chat_id, last_activity, message_count)
            VALUES (?, ?, ?, COALESCE((SELECT message_count FROM user_activity WHERE user_id = ?), 0) + 1)
        """
        current_time = datetime.now().isoformat()
        self.db.execute_update(query, (user_id, chat_id, current_time, user_id))
    
    def get_user_activity(self, user_id: int, chat_id: int) -> Optional[UserActivity]:
        """
        Get user activity information.
        
        Args:
            user_id: User ID
            chat_id: Chat ID
            
        Returns:
            UserActivity object or None if not found
        """
        query = "SELECT user_id, chat_id, last_activity, message_count FROM user_activity WHERE user_id = ? AND chat_id = ?"
        rows = self.db.execute_query(query, (user_id, chat_id))
        
        if not rows:
            return None
        
        row = rows[0]
        return UserActivity(
            user_id=row['user_id'],
            chat_id=row['chat_id'],
            last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
            message_count=row['message_count']
        )
    
    def get_inactive_users(self, chat_id: int, inactive_days: int) -> List[UserActivity]:
        """
        Get users who have been inactive for specified number of days.
        
        Args:
            chat_id: Chat ID to check
            inactive_days: Number of days to consider as inactive
            
        Returns:
            List of UserActivity objects for inactive users
        """
        cutoff_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_time = cutoff_time.replace(day=cutoff_time.day - inactive_days)
        
        query = """
            SELECT user_id, chat_id, last_activity, message_count
            FROM user_activity
            WHERE chat_id = ? AND last_activity < ?
            ORDER BY last_activity ASC
        """
        rows = self.db.execute_query(query, (chat_id, cutoff_time.isoformat()))
        
        return [
            UserActivity(
                user_id=row['user_id'],
                chat_id=row['chat_id'],
                last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
                message_count=row['message_count']
            )
            for row in rows
        ]


class CustomCommandRepository(BaseRepository):
    """Repository for managing custom bot commands."""
    
    def add_custom_command(self, chat_id: int, command_name: str, response: str, created_by: int) -> int:
        """
        Add a new custom command.
        
        Args:
            chat_id: Chat ID where command is available
            command_name: Name of the command (without /)
            response: Response text for the command
            created_by: User ID who created the command
            
        Returns:
            ID of the created command
        """
        query = """
            INSERT INTO custom_commands (chat_id, command_name, response, created_by)
            VALUES (?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (chat_id, command_name, response, created_by))
    
    def get_custom_command(self, chat_id: int, command_name: str) -> Optional[CustomCommand]:
        """
        Get a custom command by name.
        
        Args:
            chat_id: Chat ID
            command_name: Command name to search for
            
        Returns:
            CustomCommand object or None if not found
        """
        query = """
            SELECT id, chat_id, command_name, response, created_by, created_at
            FROM custom_commands
            WHERE chat_id = ? AND command_name = ?
        """
        rows = self.db.execute_query(query, (chat_id, command_name))
        
        if not rows:
            return None
        
        row = rows[0]
        return CustomCommand(
            id=row['id'],
            chat_id=row['chat_id'],
            command_name=row['command_name'],
            response=row['response'],
            created_by=row['created_by'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    def get_all_custom_commands(self, chat_id: int) -> List[CustomCommand]:
        """
        Get all custom commands for a chat.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            List of CustomCommand objects
        """
        query = """
            SELECT id, chat_id, command_name, response, created_by, created_at
            FROM custom_commands
            WHERE chat_id = ?
            ORDER BY command_name ASC
        """
        rows = self.db.execute_query(query, (chat_id,))
        
        return [
            CustomCommand(
                id=row['id'],
                chat_id=row['chat_id'],
                command_name=row['command_name'],
                response=row['response'],
                created_by=row['created_by'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]
    
    def delete_custom_command(self, chat_id: int, command_name: str) -> bool:
        """
        Delete a custom command.
        
        Args:
            chat_id: Chat ID
            command_name: Command name to delete
            
        Returns:
            True if command was deleted, False otherwise
        """
        query = "DELETE FROM custom_commands WHERE chat_id = ? AND command_name = ?"
        affected_rows = self.db.execute_update(query, (chat_id, command_name))
        return affected_rows > 0


class SpamFilterRepository(BaseRepository):
    """Repository for managing spam filters."""
    
    def add_spam_filter(self, chat_id: int, filter_word: str, action: str = 'warn') -> int:
        """
        Add a new spam filter word.
        
        Args:
            chat_id: Chat ID where filter applies
            filter_word: Word or phrase to filter
            action: Action to take (warn, delete, ban)
            
        Returns:
            ID of the created filter
        """
        query = """
            INSERT INTO spam_filters (chat_id, filter_word, action)
            VALUES (?, ?, ?)
        """
        return self.db.execute_insert(query, (chat_id, filter_word.lower(), action))
    
    def get_spam_filters(self, chat_id: int) -> List[SpamFilter]:
        """
        Get all spam filters for a chat.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            List of SpamFilter objects
        """
        query = """
            SELECT id, chat_id, filter_word, action, created_at
            FROM spam_filters
            WHERE chat_id = ?
            ORDER BY id DESC
        """
        rows = self.db.execute_query(query, (chat_id,))
        
        return [
            SpamFilter(
                id=row['id'],
                chat_id=row['chat_id'],
                filter_word=row['filter_word'],
                action=row['action'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]
    
    def remove_spam_filter(self, chat_id: int, filter_word: str) -> bool:
        """
        Remove a spam filter word.
        
        Args:
            chat_id: Chat ID
            filter_word: Filter word to remove
            
        Returns:
            True if filter was removed, False otherwise
        """
        query = "DELETE FROM spam_filters WHERE chat_id = ? AND filter_word = ?"
        affected_rows = self.db.execute_update(query, (chat_id, filter_word.lower()))
        return affected_rows > 0
    
    def check_spam(self, chat_id: int, message_text: str) -> Optional[SpamFilter]:
        """
        Check if a message contains spam based on filters.
        
        Args:
            chat_id: Chat ID to check filters for
            message_text: Message text to check
            
        Returns:
            SpamFilter object if spam detected, None otherwise
        """
        filters = self.get_spam_filters(chat_id)
        message_lower = message_text.lower()
        
        for spam_filter in filters:
            if spam_filter.filter_word in message_lower:
                return spam_filter
        
        return None