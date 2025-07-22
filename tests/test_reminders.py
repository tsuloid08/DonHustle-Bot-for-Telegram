"""
Tests for reminder functionality in @donhustle_bot
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import asyncio

from telegram import Update, Chat, User, Message
from telegram.ext import ContextTypes

from database.repositories import ReminderRepository
from database.models import Reminder
from utils.theme import ThemeEngine, MessageType, ToneStyle
from handlers.commands import CommandHandler


class TestReminderCommands(unittest.TestCase):
    """Test reminder command functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.theme_engine = ThemeEngine(ToneStyle.SERIOUS)
        
        # Mock database manager and repositories
        self.db_manager_patcher = patch('database.repositories.get_database_manager')
        self.mock_db_manager = self.db_manager_patcher.start()
        
        # Mock reminder repository
        self.reminder_repo = MagicMock(spec=ReminderRepository)
        
        # Create command handler with mocked dependencies
        self.command_handler = CommandHandler(self.theme_engine)
        self.command_handler.reminder_repository = self.reminder_repo
        
        # Mock Telegram objects
        self.chat = MagicMock(spec=Chat)
        self.chat.id = 123456789
        self.chat.type = "group"
        
        self.user = MagicMock(spec=User)
        self.user.id = 987654321
        self.user.first_name = "Test"
        
        self.message = MagicMock(spec=Message)
        self.message.chat = self.chat
        self.message.from_user = self.user
        
        self.update = MagicMock(spec=Update)
        self.update.effective_chat = self.chat
        self.update.effective_user = self.user
        self.update.message = self.message
        
        self.context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    
    def tearDown(self):
        """Clean up after tests"""
        self.db_manager_patcher.stop()
    
    def test_parse_reminder_datetime(self):
        """Test parsing of reminder date and time strings"""
        # Test today
        result = self.command_handler._parse_reminder_datetime("today", "15:30")
        today = datetime.now()
        expected = today.replace(hour=15, minute=30, second=0, microsecond=0)
        self.assertEqual(result.hour, 15)
        self.assertEqual(result.minute, 30)
        self.assertEqual(result.day, today.day)
        
        # Test tomorrow
        result = self.command_handler._parse_reminder_datetime("tomorrow", "10:00")
        tomorrow = datetime.now() + timedelta(days=1)
        expected = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        self.assertEqual(result.hour, 10)
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.day, tomorrow.day)
        
        # Test specific date
        result = self.command_handler._parse_reminder_datetime("25/12", "23:59")
        today = datetime.now()
        expected = datetime(today.year, 12, 25, 23, 59)
        self.assertEqual(result.day, 25)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.hour, 23)
        self.assertEqual(result.minute, 59)
    
    def test_parse_reminder_datetime_invalid(self):
        """Test parsing invalid date and time formats"""
        # Invalid time format
        with self.assertRaises(ValueError):
            self.command_handler._parse_reminder_datetime("today", "25:30")
        
        # Invalid date format
        with self.assertRaises(ValueError):
            self.command_handler._parse_reminder_datetime("someday", "15:30")
    
    @patch('handlers.commands.datetime')
    async def test_handle_remind_one_time(self, mock_datetime):
        """Test handling one-time reminder command"""
        # Mock current time
        now = datetime(2025, 7, 21, 10, 0)
        mock_datetime.now.return_value = now
        
        # Set up command arguments
        self.context.args = ["tomorrow", "15:30", "Team", "meeting"]
        
        # Mock reminder creation
        self.reminder_repo.create_reminder.return_value = 1
        
        # Call the handler
        await self.command_handler.handle_remind(self.update, self.context)
        
        # Check if reminder was created with correct parameters
        self.reminder_repo.create_reminder.assert_called_once()
        args, kwargs = self.reminder_repo.create_reminder.call_args
        
        self.assertEqual(kwargs["chat_id"], self.chat.id)
        self.assertEqual(kwargs["user_id"], self.user.id)
        self.assertEqual(kwargs["message"], "Team meeting")
        self.assertEqual(kwargs["is_recurring"], False)
        self.assertIsNone(kwargs["recurrence_pattern"])
        
        # Check that the remind_time is tomorrow at 15:30
        expected_time = now + timedelta(days=1)
        expected_time = expected_time.replace(hour=15, minute=30, second=0, microsecond=0)
        self.assertEqual(kwargs["remind_time"], expected_time)
        
        # Check that a response was sent
        self.update.message.reply_text.assert_called_once()
    
    @patch('handlers.commands.datetime')
    async def test_handle_remind_weekly(self, mock_datetime):
        """Test handling weekly recurring reminder command"""
        # Mock current time (Monday)
        now = datetime(2025, 7, 21, 10, 0)
        mock_datetime.now.return_value = now
        
        # Set up command arguments for weekly reminder on Wednesday
        self.context.args = ["weekly", "wednesday", "10:00", "Weekly", "report", "submission"]
        
        # Mock reminder creation
        self.reminder_repo.create_reminder.return_value = 1
        
        # Call the handler
        await self.command_handler.handle_remind(self.update, self.context)
        
        # Check if reminder was created with correct parameters
        self.reminder_repo.create_reminder.assert_called_once()
        args, kwargs = self.reminder_repo.create_reminder.call_args
        
        self.assertEqual(kwargs["chat_id"], self.chat.id)
        self.assertEqual(kwargs["user_id"], self.user.id)
        self.assertEqual(kwargs["message"], "Weekly report submission")
        self.assertEqual(kwargs["is_recurring"], True)
        self.assertEqual(kwargs["recurrence_pattern"], "weekly")
        
        # Check that a response was sent
        self.update.message.reply_text.assert_called_once()
    
    async def test_handle_reminders_empty(self):
        """Test handling reminders command with no active reminders"""
        # Mock empty reminders list
        self.reminder_repo.get_active_reminders.return_value = []
        
        # Call the handler
        await self.command_handler.handle_reminders(self.update, self.context)
        
        # Check that the repository was called with correct chat ID
        self.reminder_repo.get_active_reminders.assert_called_once_with(self.chat.id)
        
        # Check that a "no reminders" message was sent
        self.update.message.reply_text.assert_called_once()
        args, kwargs = self.update.message.reply_text.call_args
        self.assertIn("No hay recordatorios activos", args[0])
    
    async def test_handle_reminders_with_data(self):
        """Test handling reminders command with active reminders"""
        # Create sample reminders
        tomorrow = datetime.now() + timedelta(days=1)
        next_week = datetime.now() + timedelta(days=7)
        
        reminders = [
            Reminder(
                id=1,
                chat_id=self.chat.id,
                user_id=self.user.id,
                message="Team meeting",
                remind_time=tomorrow.replace(hour=15, minute=30),
                is_recurring=False,
                recurrence_pattern=None,
                is_active=True
            ),
            Reminder(
                id=2,
                chat_id=self.chat.id,
                user_id=self.user.id,
                message="Weekly report",
                remind_time=next_week.replace(hour=10, minute=0),
                is_recurring=True,
                recurrence_pattern="weekly",
                is_active=True
            )
        ]
        
        # Mock reminders list
        self.reminder_repo.get_active_reminders.return_value = reminders
        
        # Call the handler
        await self.command_handler.handle_reminders(self.update, self.context)
        
        # Check that the repository was called with correct chat ID
        self.reminder_repo.get_active_reminders.assert_called_once_with(self.chat.id)
        
        # Check that a message with reminders was sent
        self.update.message.reply_text.assert_called_once()
        args, kwargs = self.update.message.reply_text.call_args
        
        # Check that both reminders are in the message
        self.assertIn("Team meeting", args[0])
        self.assertIn("Weekly report", args[0])


if __name__ == '__main__':
    unittest.main()