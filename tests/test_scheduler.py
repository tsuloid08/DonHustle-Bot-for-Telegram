"""
Tests for scheduler functionality in @donhustle_bot
"""

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from datetime import datetime, timedelta

from telegram.ext import Application

from utils.scheduler import ReminderScheduler
from utils.theme import ThemeEngine, ToneStyle
from database.models import Reminder


class TestReminderScheduler(unittest.TestCase):
    """Test reminder scheduler functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.theme_engine = ThemeEngine(ToneStyle.SERIOUS)
        
        # Mock application
        self.application = MagicMock(spec=Application)
        self.application.bot = MagicMock()
        self.application.bot.send_message = AsyncMock()
        
        # Mock database manager and repositories
        self.db_manager_patcher = patch('utils.scheduler.get_database_manager')
        self.mock_db_manager = self.db_manager_patcher.start()
        
        # Mock reminder repository
        self.reminder_repo = MagicMock()
        
        # Create scheduler with mocked dependencies
        self.scheduler = ReminderScheduler(self.application, self.theme_engine)
        self.scheduler.reminder_repository = self.reminder_repo
    
    def tearDown(self):
        """Clean up after tests"""
        self.db_manager_patcher.stop()
    
    async def test_check_reminders_empty(self):
        """Test checking reminders when none are due"""
        # Mock empty due reminders list
        self.reminder_repo.get_due_reminders.return_value = []
        
        # Call the check method
        await self.scheduler._check_reminders()
        
        # Verify repository was called
        self.reminder_repo.get_due_reminders.assert_called_once()
        
        # Verify no messages were sent
        self.application.bot.send_message.assert_not_called()
    
    async def test_check_reminders_one_time(self):
        """Test checking reminders with a one-time reminder due"""
        # Create a sample one-time reminder
        now = datetime.now()
        reminder = Reminder(
            id=1,
            chat_id=123456789,
            user_id=987654321,
            message="Team meeting",
            remind_time=now,
            is_recurring=False,
            recurrence_pattern=None,
            is_active=True
        )
        
        # Mock due reminders list
        self.reminder_repo.get_due_reminders.return_value = [reminder]
        
        # Call the check method
        await self.scheduler._check_reminders()
        
        # Verify repository was called
        self.reminder_repo.get_due_reminders.assert_called_once()
        
        # Verify reminder was deactivated
        self.reminder_repo.deactivate_reminder.assert_called_once_with(reminder.id)
        
        # Verify message was sent
        self.application.bot.send_message.assert_called_once()
        args, kwargs = self.application.bot.send_message.call_args
        self.assertEqual(kwargs["chat_id"], reminder.chat_id)
        self.assertIn(reminder.message, kwargs["text"])
    
    async def test_check_reminders_recurring(self):
        """Test checking reminders with a recurring reminder due"""
        # Create a sample recurring reminder
        now = datetime.now()
        reminder = Reminder(
            id=1,
            chat_id=123456789,
            user_id=987654321,
            message="Weekly report",
            remind_time=now,
            is_recurring=True,
            recurrence_pattern="weekly",
            is_active=True
        )
        
        # Mock due reminders list
        self.reminder_repo.get_due_reminders.return_value = [reminder]
        
        # Call the check method
        await self.scheduler._check_reminders()
        
        # Verify repository was called
        self.reminder_repo.get_due_reminders.assert_called_once()
        
        # Verify new reminder was created for next week
        self.reminder_repo.create_reminder.assert_called_once()
        args, kwargs = self.reminder_repo.create_reminder.call_args
        
        self.assertEqual(kwargs["chat_id"], reminder.chat_id)
        self.assertEqual(kwargs["user_id"], reminder.user_id)
        self.assertEqual(kwargs["message"], reminder.message)
        self.assertEqual(kwargs["is_recurring"], True)
        self.assertEqual(kwargs["recurrence_pattern"], "weekly")
        
        # Check that the new reminder time is 7 days later
        expected_time = reminder.remind_time + timedelta(days=7)
        self.assertEqual(kwargs["remind_time"], expected_time)
        
        # Verify reminder was NOT deactivated (it's recurring)
        self.reminder_repo.deactivate_reminder.assert_not_called()
        
        # Verify message was sent
        self.application.bot.send_message.assert_called_once()
        args, kwargs = self.application.bot.send_message.call_args
        self.assertEqual(kwargs["chat_id"], reminder.chat_id)
        self.assertIn(reminder.message, kwargs["text"])
    
    @patch('utils.scheduler.asyncio.sleep', new_callable=AsyncMock)
    async def test_run_scheduler(self, mock_sleep):
        """Test the scheduler main loop"""
        # Mock check_reminders to track calls
        self.scheduler._check_reminders = AsyncMock()
        
        # Set up to run once and then stop
        self.scheduler.is_running = True
        mock_sleep.side_effect = [None, Exception("Stop test")]  # Run once, then raise exception to stop
        
        # Run the scheduler (will stop after one iteration due to the exception)
        with self.assertRaises(Exception):
            await self.scheduler._run_scheduler(60)
        
        # Verify check_reminders was called
        self.scheduler._check_reminders.assert_called_once()
        
        # Verify sleep was called with correct interval
        mock_sleep.assert_called_once_with(60)


if __name__ == '__main__':
    unittest.main()