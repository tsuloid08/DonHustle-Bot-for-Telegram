"""
Integration tests for reminder execution system in @donhustle_bot
"""

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from datetime import datetime, timedelta

from telegram.ext import Application

from utils.scheduler import ReminderScheduler
from utils.theme import ThemeEngine, ToneStyle, MessageType
from database.models import Reminder
from database.repositories import ReminderRepository


class TestReminderExecution(unittest.IsolatedAsyncioTestCase):
    """Integration tests for reminder execution system"""
    
    async def asyncSetUp(self):
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
        self.reminder_repo = MagicMock(spec=ReminderRepository)
        
        # Create scheduler with mocked dependencies
        self.scheduler = ReminderScheduler(self.application, self.theme_engine)
        self.scheduler.reminder_repository = self.reminder_repo
    
    async def asyncTearDown(self):
        """Clean up after tests"""
        self.db_manager_patcher.stop()
    
    async def test_reminder_execution_flow(self):
        """Test the complete reminder execution flow"""
        # Create test reminders
        now = datetime.now()
        
        # One-time reminder
        one_time_reminder = Reminder(
            id=1,
            chat_id=123456789,
            user_id=987654321,
            message="Team meeting",
            remind_time=now,
            is_recurring=False,
            recurrence_pattern=None,
            is_active=True
        )
        
        # Recurring reminder
        recurring_reminder = Reminder(
            id=2,
            chat_id=123456789,
            user_id=987654321,
            message="Weekly report",
            remind_time=now,
            is_recurring=True,
            recurrence_pattern="weekly",
            is_active=True
        )
        
        # Set up repository mock
        self.reminder_repo.get_due_reminders.return_value = [one_time_reminder, recurring_reminder]
        self.reminder_repo.create_reminder.return_value = 3  # ID for new recurring reminder
        
        # Run the reminder check
        await self.scheduler._check_reminders()
        
        # Verify reminders were processed correctly
        
        # 1. Both reminders should have notifications sent
        self.assertEqual(self.application.bot.send_message.call_count, 2)
        
        # 2. One-time reminder should be deactivated
        self.reminder_repo.deactivate_reminder.assert_called_once_with(one_time_reminder.id)
        
        # 3. Recurring reminder should create a new reminder for next week
        self.reminder_repo.create_reminder.assert_called_once()
        args, kwargs = self.reminder_repo.create_reminder.call_args
        
        self.assertEqual(kwargs["chat_id"], recurring_reminder.chat_id)
        self.assertEqual(kwargs["user_id"], recurring_reminder.user_id)
        self.assertEqual(kwargs["message"], recurring_reminder.message)
        self.assertEqual(kwargs["is_recurring"], True)
        self.assertEqual(kwargs["recurrence_pattern"], "weekly")
        
        # Check that the new reminder time is 7 days later
        expected_time = recurring_reminder.remind_time + timedelta(days=7)
        self.assertEqual(kwargs["remind_time"], expected_time)
    
    async def test_duplicate_reminder_prevention(self):
        """Test that reminders aren't processed multiple times"""
        # Create a test reminder
        now = datetime.now()
        reminder = Reminder(
            id=1,
            chat_id=123456789,
            user_id=987654321,
            message="Test reminder",
            remind_time=now,
            is_recurring=False,
            recurrence_pattern=None,
            is_active=True
        )
        
        # Set up repository mock to return the same reminder twice
        self.reminder_repo.get_due_reminders.return_value = [reminder]
        
        # Run the reminder check twice
        await self.scheduler._check_reminders()
        await self.scheduler._check_reminders()
        
        # Verify the reminder was only processed once
        self.application.bot.send_message.assert_called_once()
        self.reminder_repo.deactivate_reminder.assert_called_once_with(reminder.id)
    
    async def test_reminder_message_formatting(self):
        """Test that reminder messages are formatted correctly"""
        # Create a test reminder
        now = datetime.now()
        reminder = Reminder(
            id=1,
            chat_id=123456789,
            user_id=987654321,
            message="Important meeting",
            remind_time=now,
            is_recurring=False,
            recurrence_pattern=None,
            is_active=True
        )
        
        # Set up repository mock
        self.reminder_repo.get_due_reminders.return_value = [reminder]
        
        # Run the reminder check
        await self.scheduler._check_reminders()
        
        # Verify the message was formatted correctly
        self.application.bot.send_message.assert_called_once()
        args, kwargs = self.application.bot.send_message.call_args
        
        self.assertEqual(kwargs["chat_id"], reminder.chat_id)
        self.assertIn("RECORDATORIO DE LA FAMILIA", kwargs["text"])
        self.assertIn(reminder.message, kwargs["text"])
        self.assertIn(f"tg://user?id={reminder.user_id}", kwargs["text"])
    
    async def test_error_handling(self):
        """Test error handling during reminder processing"""
        # Create a test reminder
        now = datetime.now()
        reminder = Reminder(
            id=1,
            chat_id=123456789,
            user_id=987654321,
            message="Test reminder",
            remind_time=now,
            is_recurring=False,
            recurrence_pattern=None,
            is_active=True
        )
        
        # Set up repository mock
        self.reminder_repo.get_due_reminders.return_value = [reminder]
        
        # Make send_message raise an exception
        self.application.bot.send_message.side_effect = Exception("Test error")
        
        # Run the reminder check (should not raise exception)
        await self.scheduler._check_reminders()
        
        # Verify the error was handled
        self.application.bot.send_message.assert_called_once()
        self.reminder_repo.deactivate_reminder.assert_not_called()  # Should not deactivate on error
    
    async def test_get_upcoming_reminders(self):
        """Test getting upcoming reminders for a chat"""
        # Create test reminders
        now = datetime.now()
        reminders = [
            Reminder(
                id=1,
                chat_id=123456789,
                user_id=987654321,
                message="First reminder",
                remind_time=now + timedelta(hours=1),
                is_recurring=False,
                recurrence_pattern=None,
                is_active=True
            ),
            Reminder(
                id=2,
                chat_id=123456789,
                user_id=987654321,
                message="Second reminder",
                remind_time=now + timedelta(hours=2),
                is_recurring=False,
                recurrence_pattern=None,
                is_active=True
            ),
            Reminder(
                id=3,
                chat_id=123456789,
                user_id=987654321,
                message="Third reminder",
                remind_time=now + timedelta(hours=3),
                is_recurring=True,
                recurrence_pattern="weekly",
                is_active=True
            )
        ]
        
        # Set up repository mock
        self.reminder_repo.get_active_reminders.return_value = reminders
        
        # Get upcoming reminders
        result = self.scheduler.get_upcoming_reminders(123456789, limit=2)
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)  # First reminder (earliest)
        self.assertEqual(result[1].id, 2)  # Second reminder


if __name__ == '__main__':
    unittest.main()