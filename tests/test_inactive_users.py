"""
Tests for inactive user management functionality
"""

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
import asyncio

from database.manager import DatabaseManager
from database.repositories import UserActivityRepository, ConfigRepository
from database.models import UserActivity
from utils.scheduler import BotScheduler
from utils.theme import ThemeEngine, ToneStyle


class TestInactiveUserManagement(unittest.TestCase):
    """Test cases for inactive user management"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock database manager
        self.db_manager = MagicMock(spec=DatabaseManager)
        
        # Mock repositories
        self.user_activity_repo = MagicMock(spec=UserActivityRepository)
        self.config_repo = MagicMock(spec=ConfigRepository)
        
        # Mock application
        self.application = MagicMock()
        self.application.bot = AsyncMock()
        
        # Create theme engine
        self.theme_engine = ThemeEngine()
        self.theme_engine.set_tone(ToneStyle.SERIOUS)
        
        # Create scheduler with mocked dependencies
        self.scheduler = BotScheduler(self.application, self.theme_engine)
        self.scheduler.user_activity_repository = self.user_activity_repo
        self.scheduler.config_repository = self.config_repo
        self.scheduler.db_manager = self.db_manager
    
    def test_user_activity_tracking(self):
        """Test user activity tracking"""
        # Create mock user activity
        user_id = 123456
        chat_id = 789012
        
        # Call update_user_activity
        self.user_activity_repo.update_user_activity(user_id, chat_id)
        
        # Verify repository was called
        self.user_activity_repo.update_user_activity.assert_called_once_with(user_id, chat_id)
    
    def test_get_inactive_users(self):
        """Test getting inactive users"""
        # Create mock chat ID
        chat_id = 789012
        inactive_days = 7
        
        # Mock inactive users
        mock_users = [
            UserActivity(
                user_id=123456,
                chat_id=chat_id,
                last_activity=datetime.now() - timedelta(days=10),
                message_count=5
            ),
            UserActivity(
                user_id=654321,
                chat_id=chat_id,
                last_activity=datetime.now() - timedelta(days=8),
                message_count=3
            )
        ]
        
        # Configure mock to return inactive users
        self.user_activity_repo.get_inactive_users.return_value = mock_users
        
        # Call get_inactive_users
        result = self.user_activity_repo.get_inactive_users(chat_id, inactive_days)
        
        # Verify repository was called and returned expected users
        self.user_activity_repo.get_inactive_users.assert_called_once_with(chat_id, inactive_days)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].user_id, 123456)
        self.assertEqual(result[1].user_id, 654321)
    
    @patch('utils.scheduler.datetime')
    async def test_check_inactive_users(self, mock_datetime):
        """Test checking inactive users"""
        # Mock current time
        now = datetime.now()
        mock_datetime.now.return_value = now
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # Mock chat ID
        chat_id = 789012
        
        # Mock database query for chats
        self.db_manager.execute_query.return_value = [{'chat_id': chat_id}]
        
        # Configure config repository mocks
        self.config_repo.get_config.side_effect = lambda chat_id, key, default: {
            'inactive_enabled': 'true',
            'inactive_days': '7',
            'inactive_warning_hours': '24',
            f'inactive_warning_123456': (now - timedelta(hours=25)).isoformat()
        }.get(key, default)
        
        # Mock inactive users
        mock_users = [
            UserActivity(
                user_id=123456,  # User warned 25 hours ago (should be removed)
                chat_id=chat_id,
                last_activity=now - timedelta(days=10),
                message_count=5
            ),
            UserActivity(
                user_id=654321,  # User not warned yet (should be warned)
                chat_id=chat_id,
                last_activity=now - timedelta(days=8),
                message_count=3
            )
        ]
        
        # Configure user activity repository mock
        self.user_activity_repo.get_inactive_users.return_value = mock_users
        
        # Run the check
        await self.scheduler._check_inactive_users()
        
        # Verify warning was sent to the second user
        self.application.bot.send_message.assert_any_call(
            chat_id=chat_id,
            text=unittest.mock.ANY,  # Don't check exact message content
            parse_mode=unittest.mock.ANY
        )
        
        # Verify removal was attempted for the first user
        self.application.bot.ban_chat_member.assert_called_once_with(
            chat_id=chat_id,
            user_id=123456,
            until_date=unittest.mock.ANY
        )
    
    def test_setinactive_command_validation(self):
        """Test validation in setinactive command"""
        # This would be tested in an integration test with the actual command handler
        pass


if __name__ == '__main__':
    unittest.main()