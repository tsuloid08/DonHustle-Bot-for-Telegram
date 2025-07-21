"""
Unit tests for database repositories
Tests all CRUD operations and business logic for repository classes
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from database import (
    DatabaseManager, QuoteRepository, MessageRepository, ReminderRepository,
    ConfigRepository, UserActivityRepository, CustomCommandRepository, SpamFilterRepository
)


class TestRepositories(unittest.TestCase):
    """Test suite for all repository classes."""
    
    def setUp(self):
        """Set up test database for each test."""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database manager with test database
        self.db_manager = DatabaseManager(self.temp_db.name)
        
        # Initialize repositories
        self.quote_repo = QuoteRepository(self.db_manager)
        self.message_repo = MessageRepository(self.db_manager)
        self.reminder_repo = ReminderRepository(self.db_manager)
        self.config_repo = ConfigRepository(self.db_manager)
        self.activity_repo = UserActivityRepository(self.db_manager)
        self.command_repo = CustomCommandRepository(self.db_manager)
        self.spam_repo = SpamFilterRepository(self.db_manager)
    
    def tearDown(self):
        """Clean up test database after each test."""
        self.db_manager.close()
        os.unlink(self.temp_db.name)


class TestQuoteRepository(TestRepositories):
    """Test cases for QuoteRepository."""
    
    def test_add_quote(self):
        """Test adding a new quote."""
        quote_text = "El éxito es la suma de pequeños esfuerzos repetidos día tras día."
        quote_id = self.quote_repo.add_quote(quote_text)
        
        self.assertIsInstance(quote_id, int)
        self.assertGreater(quote_id, 0)
    
    def test_get_all_quotes(self):
        """Test retrieving all quotes."""
        # Add test quotes
        quotes = [
            "La familia es todo, capo.",
            "En los negocios, la lealtad es oro.",
            "Un verdadero don nunca muestra debilidad."
        ]
        
        for quote in quotes:
            self.quote_repo.add_quote(quote)
        
        # Retrieve all quotes
        all_quotes = self.quote_repo.get_all_quotes()
        
        self.assertEqual(len(all_quotes), 3)
        self.assertEqual(all_quotes[0].quote, quotes[2])  # Most recent first
        self.assertEqual(all_quotes[2].quote, quotes[0])  # Oldest last
    
    def test_get_quote_by_id(self):
        """Test retrieving a specific quote by ID."""
        quote_text = "Te haré una oferta que no podrás rechazar."
        quote_id = self.quote_repo.add_quote(quote_text)
        
        retrieved_quote = self.quote_repo.get_quote_by_id(quote_id)
        
        self.assertIsNotNone(retrieved_quote)
        self.assertEqual(retrieved_quote.quote, quote_text)
        self.assertEqual(retrieved_quote.id, quote_id)
    
    def test_get_quote_by_id_not_found(self):
        """Test retrieving a non-existent quote."""
        retrieved_quote = self.quote_repo.get_quote_by_id(999)
        self.assertIsNone(retrieved_quote)
    
    def test_delete_quote(self):
        """Test deleting a quote."""
        quote_text = "Los negocios son negocios, nada personal."
        quote_id = self.quote_repo.add_quote(quote_text)
        
        # Delete the quote
        result = self.quote_repo.delete_quote(quote_id)
        self.assertTrue(result)
        
        # Verify it's gone
        retrieved_quote = self.quote_repo.get_quote_by_id(quote_id)
        self.assertIsNone(retrieved_quote)
    
    def test_delete_quote_not_found(self):
        """Test deleting a non-existent quote."""
        result = self.quote_repo.delete_quote(999)
        self.assertFalse(result)
    
    def test_clear_all_quotes(self):
        """Test clearing all quotes."""
        # Add some quotes
        for i in range(5):
            self.quote_repo.add_quote(f"Quote {i}")
        
        # Clear all quotes
        deleted_count = self.quote_repo.clear_all_quotes()
        self.assertEqual(deleted_count, 5)
        
        # Verify they're all gone
        all_quotes = self.quote_repo.get_all_quotes()
        self.assertEqual(len(all_quotes), 0)
    
    def test_get_random_quote(self):
        """Test getting a random quote."""
        # Test with no quotes
        random_quote = self.quote_repo.get_random_quote()
        self.assertIsNone(random_quote)
        
        # Add quotes and test
        quotes = ["Quote 1", "Quote 2", "Quote 3"]
        for quote in quotes:
            self.quote_repo.add_quote(quote)
        
        random_quote = self.quote_repo.get_random_quote()
        self.assertIsNotNone(random_quote)
        self.assertIn(random_quote.quote, quotes)


class TestMessageRepository(TestRepositories):
    """Test cases for MessageRepository."""
    
    def test_save_message(self):
        """Test saving a message."""
        message_id = self.message_repo.save_message(
            chat_id=-123456,
            message_id=789,
            content="Important business message",
            saved_by=12345,
            tag="business"
        )
        
        self.assertIsInstance(message_id, int)
        self.assertGreater(message_id, 0)
    
    def test_get_saved_messages(self):
        """Test retrieving saved messages for a chat."""
        chat_id = -123456
        
        # Save test messages
        messages = [
            ("Message 1", "tag1"),
            ("Message 2", "tag2"),
            ("Message 3", None)
        ]
        
        for content, tag in messages:
            self.message_repo.save_message(chat_id, 100, content, 12345, tag)
        
        # Retrieve messages
        saved_messages = self.message_repo.get_saved_messages(chat_id)
        
        self.assertEqual(len(saved_messages), 3)
        self.assertEqual(saved_messages[0].content, "Message 3")  # Most recent first
    
    def test_get_messages_by_tag(self):
        """Test retrieving messages by tag."""
        chat_id = -123456
        
        # Save messages with different tags
        self.message_repo.save_message(chat_id, 100, "Business msg 1", 12345, "business")
        self.message_repo.save_message(chat_id, 101, "Personal msg", 12345, "personal")
        self.message_repo.save_message(chat_id, 102, "Business msg 2", 12345, "business")
        
        # Get business messages
        business_messages = self.message_repo.get_messages_by_tag(chat_id, "business")
        
        self.assertEqual(len(business_messages), 2)
        self.assertEqual(business_messages[0].content, "Business msg 2")  # Most recent first
        self.assertEqual(business_messages[1].content, "Business msg 1")


class TestReminderRepository(TestRepositories):
    """Test cases for ReminderRepository."""
    
    def test_create_reminder(self):
        """Test creating a reminder."""
        remind_time = datetime.now() + timedelta(hours=1)
        
        reminder_id = self.reminder_repo.create_reminder(
            chat_id=-123456,
            user_id=12345,
            message="Don't forget the meeting",
            remind_time=remind_time
        )
        
        self.assertIsInstance(reminder_id, int)
        self.assertGreater(reminder_id, 0)
    
    def test_get_active_reminders(self):
        """Test retrieving active reminders."""
        chat_id = -123456
        remind_time = datetime.now() + timedelta(hours=1)
        
        # Create test reminders
        self.reminder_repo.create_reminder(chat_id, 12345, "Reminder 1", remind_time)
        self.reminder_repo.create_reminder(chat_id, 12346, "Reminder 2", remind_time + timedelta(hours=1))
        
        # Get active reminders
        active_reminders = self.reminder_repo.get_active_reminders(chat_id)
        
        self.assertEqual(len(active_reminders), 2)
        self.assertEqual(active_reminders[0].message, "Reminder 1")  # Earliest first
    
    def test_get_due_reminders(self):
        """Test retrieving due reminders."""
        chat_id = -123456
        past_time = datetime.now() - timedelta(minutes=30)
        future_time = datetime.now() + timedelta(hours=1)
        
        # Create reminders
        due_id = self.reminder_repo.create_reminder(chat_id, 12345, "Due reminder", past_time)
        self.reminder_repo.create_reminder(chat_id, 12346, "Future reminder", future_time)
        
        # Get due reminders
        due_reminders = self.reminder_repo.get_due_reminders(datetime.now())
        
        self.assertEqual(len(due_reminders), 1)
        self.assertEqual(due_reminders[0].message, "Due reminder")
    
    def test_deactivate_reminder(self):
        """Test deactivating a reminder."""
        remind_time = datetime.now() + timedelta(hours=1)
        reminder_id = self.reminder_repo.create_reminder(-123456, 12345, "Test reminder", remind_time)
        
        # Deactivate reminder
        result = self.reminder_repo.deactivate_reminder(reminder_id)
        self.assertTrue(result)
        
        # Verify it's not in active reminders
        active_reminders = self.reminder_repo.get_active_reminders(-123456)
        self.assertEqual(len(active_reminders), 0)


class TestConfigRepository(TestRepositories):
    """Test cases for ConfigRepository."""
    
    def test_set_and_get_config(self):
        """Test setting and getting configuration values."""
        chat_id = -123456
        
        # Set config
        self.config_repo.set_config(chat_id, "quote_interval", "50")
        self.config_repo.set_config(chat_id, "bot_style", "serious")
        
        # Get config
        interval = self.config_repo.get_config(chat_id, "quote_interval")
        style = self.config_repo.get_config(chat_id, "bot_style")
        
        self.assertEqual(interval, "50")
        self.assertEqual(style, "serious")
    
    def test_get_config_with_default(self):
        """Test getting config with default value."""
        result = self.config_repo.get_config(-123456, "nonexistent", "default_value")
        self.assertEqual(result, "default_value")
    
    def test_get_all_config(self):
        """Test getting all configuration for a chat."""
        chat_id = -123456
        
        # Set multiple configs
        configs = {
            "quote_interval": "50",
            "bot_style": "humorous",
            "inactive_days": "7"
        }
        
        for key, value in configs.items():
            self.config_repo.set_config(chat_id, key, value)
        
        # Get all configs
        all_configs = self.config_repo.get_all_config(chat_id)
        
        self.assertEqual(all_configs, configs)
    
    def test_delete_config(self):
        """Test deleting a configuration value."""
        chat_id = -123456
        
        # Set and then delete config
        self.config_repo.set_config(chat_id, "test_key", "test_value")
        result = self.config_repo.delete_config(chat_id, "test_key")
        
        self.assertTrue(result)
        
        # Verify it's gone
        value = self.config_repo.get_config(chat_id, "test_key")
        self.assertIsNone(value)


class TestUserActivityRepository(TestRepositories):
    """Test cases for UserActivityRepository."""
    
    def test_update_user_activity(self):
        """Test updating user activity."""
        user_id = 12345
        chat_id = -123456
        
        # Update activity
        self.activity_repo.update_user_activity(user_id, chat_id)
        
        # Get activity
        activity = self.activity_repo.get_user_activity(user_id, chat_id)
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity.user_id, user_id)
        self.assertEqual(activity.chat_id, chat_id)
        self.assertEqual(activity.message_count, 1)
    
    def test_multiple_activity_updates(self):
        """Test multiple activity updates increment message count."""
        user_id = 12345
        chat_id = -123456
        
        # Update activity multiple times
        for _ in range(5):
            self.activity_repo.update_user_activity(user_id, chat_id)
        
        # Check message count
        activity = self.activity_repo.get_user_activity(user_id, chat_id)
        self.assertEqual(activity.message_count, 5)
    
    def test_get_inactive_users(self):
        """Test getting inactive users."""
        chat_id = -123456
        
        # Create user activities with different timestamps
        old_time = datetime.now() - timedelta(days=10)
        recent_time = datetime.now() - timedelta(hours=1)
        
        # Manually insert old activity
        query = """
            INSERT INTO user_activity (user_id, chat_id, last_activity, message_count)
            VALUES (?, ?, ?, ?)
        """
        self.db_manager.execute_update(query, (12345, chat_id, old_time.isoformat(), 5))
        self.db_manager.execute_update(query, (12346, chat_id, recent_time.isoformat(), 3))
        
        # Get inactive users (7+ days)
        inactive_users = self.activity_repo.get_inactive_users(chat_id, 7)
        
        self.assertEqual(len(inactive_users), 1)
        self.assertEqual(inactive_users[0].user_id, 12345)


class TestCustomCommandRepository(TestRepositories):
    """Test cases for CustomCommandRepository."""
    
    def test_add_custom_command(self):
        """Test adding a custom command."""
        command_id = self.command_repo.add_custom_command(
            chat_id=-123456,
            command_name="familia",
            response="La familia es sagrada, capo.",
            created_by=12345
        )
        
        self.assertIsInstance(command_id, int)
        self.assertGreater(command_id, 0)
    
    def test_get_custom_command(self):
        """Test retrieving a custom command."""
        chat_id = -123456
        
        # Add command
        self.command_repo.add_custom_command(
            chat_id, "negocio", "Los negocios van bien, don.", 12345
        )
        
        # Get command
        command = self.command_repo.get_custom_command(chat_id, "negocio")
        
        self.assertIsNotNone(command)
        self.assertEqual(command.command_name, "negocio")
        self.assertEqual(command.response, "Los negocios van bien, don.")
    
    def test_get_all_custom_commands(self):
        """Test getting all custom commands for a chat."""
        chat_id = -123456
        
        # Add multiple commands
        commands = [
            ("familia", "La familia es todo"),
            ("respeto", "El respeto se gana"),
            ("lealtad", "La lealtad es oro")
        ]
        
        for name, response in commands:
            self.command_repo.add_custom_command(chat_id, name, response, 12345)
        
        # Get all commands
        all_commands = self.command_repo.get_all_custom_commands(chat_id)
        
        self.assertEqual(len(all_commands), 3)
        # Should be sorted by command name
        self.assertEqual(all_commands[0].command_name, "familia")
        self.assertEqual(all_commands[1].command_name, "lealtad")
        self.assertEqual(all_commands[2].command_name, "respeto")
    
    def test_delete_custom_command(self):
        """Test deleting a custom command."""
        chat_id = -123456
        
        # Add and delete command
        self.command_repo.add_custom_command(chat_id, "test", "Test response", 12345)
        result = self.command_repo.delete_custom_command(chat_id, "test")
        
        self.assertTrue(result)
        
        # Verify it's gone
        command = self.command_repo.get_custom_command(chat_id, "test")
        self.assertIsNone(command)


class TestSpamFilterRepository(TestRepositories):
    """Test cases for SpamFilterRepository."""
    
    def test_add_spam_filter(self):
        """Test adding a spam filter."""
        filter_id = self.spam_repo.add_spam_filter(
            chat_id=-123456,
            filter_word="spam",
            action="delete"
        )
        
        self.assertIsInstance(filter_id, int)
        self.assertGreater(filter_id, 0)
    
    def test_get_spam_filters(self):
        """Test getting spam filters for a chat."""
        chat_id = -123456
        
        # Add filters
        filters = [
            ("badword1", "warn"),
            ("badword2", "delete"),
            ("badword3", "ban")
        ]
        
        for word, action in filters:
            self.spam_repo.add_spam_filter(chat_id, word, action)
        
        # Get filters
        spam_filters = self.spam_repo.get_spam_filters(chat_id)
        
        self.assertEqual(len(spam_filters), 3)
        # Most recent first
        self.assertEqual(spam_filters[0].filter_word, "badword3")
    
    def test_remove_spam_filter(self):
        """Test removing a spam filter."""
        chat_id = -123456
        
        # Add and remove filter
        self.spam_repo.add_spam_filter(chat_id, "testword", "warn")
        result = self.spam_repo.remove_spam_filter(chat_id, "testword")
        
        self.assertTrue(result)
        
        # Verify it's gone
        filters = self.spam_repo.get_spam_filters(chat_id)
        self.assertEqual(len(filters), 0)
    
    def test_check_spam(self):
        """Test spam detection in messages."""
        chat_id = -123456
        
        # Add spam filters
        self.spam_repo.add_spam_filter(chat_id, "spam", "delete")
        self.spam_repo.add_spam_filter(chat_id, "badword", "warn")
        
        # Test spam detection
        spam_result = self.spam_repo.check_spam(chat_id, "This message contains spam content")
        self.assertIsNotNone(spam_result)
        self.assertEqual(spam_result.filter_word, "spam")
        self.assertEqual(spam_result.action, "delete")
        
        # Test clean message
        clean_result = self.spam_repo.check_spam(chat_id, "This is a clean message")
        self.assertIsNone(clean_result)
    
    def test_case_insensitive_spam_detection(self):
        """Test that spam detection is case insensitive."""
        chat_id = -123456
        
        # Add lowercase filter
        self.spam_repo.add_spam_filter(chat_id, "spam", "warn")
        
        # Test uppercase message
        result = self.spam_repo.check_spam(chat_id, "This message contains SPAM")
        self.assertIsNotNone(result)
        self.assertEqual(result.filter_word, "spam")


if __name__ == '__main__':
    unittest.main()