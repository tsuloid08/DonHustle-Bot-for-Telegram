"""
Tests for the moderation handler functionality
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from telegram import Update, Chat, User, Message

from handlers.moderation_handler import ModerationHandler
from utils.theme import ThemeEngine, ToneStyle
from database.models import SpamFilter


class TestModerationHandler(unittest.TestCase):
    """Test cases for the moderation handler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.theme_engine = ThemeEngine(ToneStyle.SERIOUS)
        
        # Mock the database repositories
        self.mock_db_manager = MagicMock()
        self.mock_spam_filter_repo = MagicMock()
        self.mock_config_repo = MagicMock()
        
        # Create moderation handler with mocked dependencies
        with patch('handlers.moderation_handler.get_database_manager', return_value=self.mock_db_manager):
            with patch('handlers.moderation_handler.SpamFilterRepository', return_value=self.mock_spam_filter_repo):
                with patch('handlers.moderation_handler.ConfigRepository', return_value=self.mock_config_repo):
                    self.moderation_handler = ModerationHandler(self.theme_engine)
        
        # Mock Telegram objects
        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = 12345
        self.mock_user.first_name = "Test User"
        self.mock_user.mention_markdown.return_value = "[Test User](tg://user?id=12345)"
        
        self.mock_chat = MagicMock(spec=Chat)
        self.mock_chat.id = 67890
        self.mock_chat.type = "group"
        
        self.mock_message = MagicMock(spec=Message)
        self.mock_message.message_id = 54321
        self.mock_message.text = "Test message"
        self.mock_message.reply_text = AsyncMock()
        self.mock_message.delete = AsyncMock()
        
        self.mock_update = MagicMock(spec=Update)
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.effective_message = self.mock_message
        self.mock_update.message = self.mock_message
        
        self.mock_context = MagicMock()
        self.mock_context.args = []
        self.mock_context.bot = MagicMock()
        self.mock_context.bot.send_message = AsyncMock()
        self.mock_context.bot.get_chat_member = AsyncMock()
        self.mock_context.bot.ban_chat_member = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_check_admin_permissions_admin(self):
        """Test admin permission check for admin user"""
        # Mock admin status
        chat_member = MagicMock()
        chat_member.status = "administrator"
        self.mock_context.bot.get_chat_member.return_value = chat_member
        
        # Check permissions
        result = await self.moderation_handler.check_admin_permissions(self.mock_update, self.mock_context)
        
        # Verify
        self.assertTrue(result)
        self.mock_context.bot.get_chat_member.assert_called_once_with(
            self.mock_chat.id, self.mock_user.id
        )
    
    @pytest.mark.asyncio
    async def test_check_admin_permissions_not_admin(self):
        """Test admin permission check for non-admin user"""
        # Mock non-admin status
        chat_member = MagicMock()
        chat_member.status = "member"
        self.mock_context.bot.get_chat_member.return_value = chat_member
        
        # Check permissions
        result = await self.moderation_handler.check_admin_permissions(self.mock_update, self.mock_context)
        
        # Verify
        self.assertFalse(result)
        self.mock_context.bot.get_chat_member.assert_called_once_with(
            self.mock_chat.id, self.mock_user.id
        )
    
    @pytest.mark.asyncio
    async def test_handle_filter_add_success(self):
        """Test adding a spam filter word successfully"""
        # Setup
        self.mock_context.args = ["badword", "warn"]
        self.moderation_handler.check_admin_permissions = AsyncMock(return_value=True)
        self.mock_spam_filter_repo.add_spam_filter.return_value = 1
        
        # Execute
        await self.moderation_handler.handle_filter_add(self.mock_update, self.mock_context)
        
        # Verify
        self.mock_spam_filter_repo.add_spam_filter.assert_called_once_with(
            self.mock_chat.id, "badword", "warn"
        )
        self.mock_message.reply_text.assert_called_once()
        
        # Check that success message was sent
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("badword", call_args)
        self.assertIn("warn", call_args)
    
    @pytest.mark.asyncio
    async def test_handle_filter_add_no_permission(self):
        """Test adding a spam filter without admin permissions"""
        # Setup
        self.mock_context.args = ["badword"]
        self.moderation_handler.check_admin_permissions = AsyncMock(return_value=False)
        
        # Execute
        await self.moderation_handler.handle_filter_add(self.mock_update, self.mock_context)
        
        # Verify
        self.mock_spam_filter_repo.add_spam_filter.assert_not_called()
        self.mock_message.reply_text.assert_called_once()
        
        # Check that warning message was sent
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("administradores", call_args)
    
    @pytest.mark.asyncio
    async def test_check_spam_message_with_spam(self):
        """Test checking a message that contains spam"""
        # Setup
        spam_filter = SpamFilter(
            id=1,
            chat_id=self.mock_chat.id,
            filter_word="badword",
            action="warn"
        )
        self.mock_message.text = "This message contains badword and should be flagged"
        self.mock_spam_filter_repo.check_spam.return_value = spam_filter
        
        # Execute
        await self.moderation_handler.check_spam_message(self.mock_update, self.mock_context)
        
        # Verify
        self.mock_spam_filter_repo.check_spam.assert_called_once_with(
            self.mock_chat.id, self.mock_message.text
        )
        self.mock_message.reply_text.assert_called_once()
        
        # Check that warning message was sent
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("Advertencia", call_args)
    
    @pytest.mark.asyncio
    async def test_check_spam_message_no_spam(self):
        """Test checking a message that doesn't contain spam"""
        # Setup
        self.mock_message.text = "This is a clean message"
        self.mock_spam_filter_repo.check_spam.return_value = None
        
        # Execute
        await self.moderation_handler.check_spam_message(self.mock_update, self.mock_context)
        
        # Verify
        self.mock_spam_filter_repo.check_spam.assert_called_once_with(
            self.mock_chat.id, self.mock_message.text
        )
        self.mock_message.reply_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_spam_message_delete_action(self):
        """Test checking a message with delete action"""
        # Setup
        spam_filter = SpamFilter(
            id=1,
            chat_id=self.mock_chat.id,
            filter_word="badword",
            action="delete"
        )
        self.mock_message.text = "This message contains badword and should be deleted"
        self.mock_spam_filter_repo.check_spam.return_value = spam_filter
        
        # Execute
        await self.moderation_handler.check_spam_message(self.mock_update, self.mock_context)
        
        # Verify
        self.mock_message.delete.assert_called_once()
        self.mock_context.bot.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_user_strikes_system(self):
        """Test the user strike system"""
        # Setup
        chat_id = 67890
        user_id = 12345
        
        # Initial strikes should be 0
        initial_strikes = self.moderation_handler.get_user_strikes(chat_id, user_id)
        self.assertEqual(initial_strikes, 0)
        
        # Add a strike
        new_strikes = self.moderation_handler.add_user_strike(chat_id, user_id)
        self.assertEqual(new_strikes, 1)
        
        # Check strikes
        current_strikes = self.moderation_handler.get_user_strikes(chat_id, user_id)
        self.assertEqual(current_strikes, 1)
        
        # Add two more strikes
        self.moderation_handler.add_user_strike(chat_id, user_id)
        final_strikes = self.moderation_handler.add_user_strike(chat_id, user_id)
        self.assertEqual(final_strikes, 3)


if __name__ == '__main__':
    unittest.main()