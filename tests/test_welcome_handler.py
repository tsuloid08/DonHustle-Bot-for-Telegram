"""
Integration tests for welcome message functionality
Tests welcome message configuration and new member detection
"""

import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
import tempfile
import os
from datetime import datetime

from telegram import Update, User, Chat, Message, ChatMember, ChatMemberUpdated
from telegram.ext import ContextTypes

from handlers.welcome_handler import (
    handle_welcome_command, handle_chat_member_update, 
    send_welcome_message, extract_status_change, get_default_welcome_message
)
from utils.theme import ThemeEngine, MessageType
from database.manager import DatabaseManager
from database.repositories import ConfigRepository


class TestWelcomeHandler(unittest.TestCase):
    """Test cases for welcome message functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database manager with test database
        self.db_manager_patcher = patch('handlers.welcome_handler.get_database_manager')
        self.mock_db_manager_func = self.db_manager_patcher.start()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.mock_db_manager_func.return_value = self.db_manager
        
        # Set up theme engine
        self.theme_engine_patcher = patch('handlers.welcome_handler.theme_engine')
        self.mock_theme_engine = self.theme_engine_patcher.start()
        self.mock_theme_engine.generate_message.return_value = "Success message"
        self.mock_theme_engine.enhance_message.side_effect = lambda msg, add_phrase: msg
        
        # Mock user and chat
        self.user = MagicMock(spec=User)
        self.user.first_name = "TestUser"
        self.user.username = "testuser"
        self.user.id = 123456789
        
        # Mock group chat
        self.group_chat = MagicMock(spec=Chat)
        self.group_chat.id = 987654321
        self.group_chat.type = "group"
        self.group_chat.title = "Test Group"
        
        # Mock context
        self.context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        self.context.bot = MagicMock()
        self.context.bot.id = 111222333
        self.context.bot.get_chat_member = AsyncMock()
        self.context.bot.send_message = AsyncMock()
    
    def tearDown(self):
        """Clean up after tests"""
        self.db_manager_patcher.stop()
        self.theme_engine_patcher.stop()
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def create_mock_update(self, is_admin=True, with_args=None):
        """Create a mock update for welcome command testing"""
        update = MagicMock(spec=Update)
        update.effective_user = self.user
        update.effective_chat = self.group_chat
        
        # Mock message
        message = MagicMock(spec=Message)
        message.reply_text = AsyncMock()
        update.message = message
        update.effective_message = message
        
        # Mock admin status
        mock_chat_member = MagicMock(spec=ChatMember)
        mock_chat_member.status = "administrator" if is_admin else "member"
        self.context.bot.get_chat_member.return_value = mock_chat_member
        
        # Add command arguments if provided
        if with_args:
            self.context.args = with_args.split()
        else:
            self.context.args = []
        
        return update
    
    def create_chat_member_update(self, old_status="left", new_status="member"):
        """Create a mock chat member update for new member testing"""
        update = MagicMock(spec=Update)
        update.effective_chat = self.group_chat
        
        # Create old chat member
        old_chat_member = MagicMock(spec=ChatMember)
        old_chat_member.status = old_status
        old_chat_member.user = self.user
        
        # Create new chat member
        new_chat_member = MagicMock(spec=ChatMember)
        new_chat_member.status = new_status
        new_chat_member.user = self.user
        
        # Create chat member updated
        chat_member_updated = MagicMock(spec=ChatMemberUpdated)
        chat_member_updated.old_chat_member = old_chat_member
        chat_member_updated.new_chat_member = new_chat_member
        chat_member_updated.chat = self.group_chat
        chat_member_updated.from_user = self.user
        chat_member_updated.date = datetime.now()
        
        update.chat_member = chat_member_updated
        
        return update
    
    @pytest.mark.asyncio
    async def test_welcome_command_no_permission(self):
        """Test /welcome command without admin permission"""
        update = self.create_mock_update(is_admin=False)
        
        await handle_welcome_command(update, self.context)
        
        # Verify error message was sent
        update.message.reply_text.assert_called_once()
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("No tienes permiso", args[0])
    
    @pytest.mark.asyncio
    async def test_welcome_command_show_default(self):
        """Test /welcome command with no arguments shows default message"""
        update = self.create_mock_update(is_admin=True)
        
        await handle_welcome_command(update, self.context)
        
        # Verify default welcome message was shown
        update.message.reply_text.assert_called_once()
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("Mensaje de bienvenida predeterminado", args[0])
        self.assertIn("Bienvenido a la familia", args[0])
    
    @pytest.mark.asyncio
    async def test_welcome_command_show_current(self):
        """Test /welcome command shows current message if configured"""
        update = self.create_mock_update(is_admin=True)
        
        # Set a welcome message in the database
        config_repo = ConfigRepository(self.db_manager)
        config_repo.set_config(self.group_chat.id, "welcome_message", "Custom welcome message")
        
        await handle_welcome_command(update, self.context)
        
        # Verify current welcome message was shown
        update.message.reply_text.assert_called_once()
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("Mensaje de bienvenida actual", args[0])
        self.assertIn("Custom welcome message", args[0])
    
    @pytest.mark.asyncio
    async def test_welcome_command_set_message(self):
        """Test /welcome command with arguments sets new welcome message"""
        update = self.create_mock_update(is_admin=True, with_args="Welcome to the family, {name}!")
        
        await handle_welcome_command(update, self.context)
        
        # Verify success message was sent
        update.message.reply_text.assert_called_once()
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("Success message", args[0])
        self.assertIn("Welcome to the family, {name}!", args[0])
        
        # Verify message was saved in database
        config_repo = ConfigRepository(self.db_manager)
        saved_message = config_repo.get_config(self.group_chat.id, "welcome_message")
        self.assertEqual(saved_message, "Welcome to the family, {name}!")
    
    @pytest.mark.asyncio
    async def test_extract_status_change(self):
        """Test status change extraction from chat member update"""
        # Test joining member
        update = self.create_chat_member_update(old_status="left", new_status="member")
        result = extract_status_change(update.chat_member)
        self.assertEqual(result, (False, True))
        
        # Test leaving member
        update = self.create_chat_member_update(old_status="member", new_status="left")
        result = extract_status_change(update.chat_member)
        self.assertEqual(result, (True, False))
        
        # Test no status change
        update = self.create_chat_member_update(old_status="member", new_status="member")
        result = extract_status_change(update.chat_member)
        self.assertEqual(result, (True, True))
    
    @pytest.mark.asyncio
    async def test_handle_chat_member_update_new_member(self):
        """Test handling new member joining"""
        update = self.create_chat_member_update(old_status="left", new_status="member")
        
        with patch('handlers.welcome_handler.send_welcome_message') as mock_send_welcome:
            mock_send_welcome.return_value = None
            await handle_chat_member_update(update, self.context)
            mock_send_welcome.assert_called_once_with(update, self.context)
    
    @pytest.mark.asyncio
    async def test_handle_chat_member_update_not_new_member(self):
        """Test handling member status change that is not joining"""
        update = self.create_chat_member_update(old_status="member", new_status="administrator")
        
        with patch('handlers.welcome_handler.send_welcome_message') as mock_send_welcome:
            await handle_chat_member_update(update, self.context)
            mock_send_welcome.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_welcome_message_default(self):
        """Test sending default welcome message to new member"""
        update = self.create_chat_member_update()
        
        await send_welcome_message(update, self.context)
        
        # Verify message was sent
        self.context.bot.send_message.assert_called_once()
        args, kwargs = self.context.bot.send_message.call_args
        self.assertEqual(kwargs["chat_id"], self.group_chat.id)
        self.assertIn("parse_mode", kwargs)
    
    @pytest.mark.asyncio
    async def test_send_welcome_message_custom(self):
        """Test sending custom welcome message to new member"""
        update = self.create_chat_member_update()
        
        # Set custom welcome message
        config_repo = ConfigRepository(self.db_manager)
        config_repo.set_config(self.group_chat.id, "welcome_message", 
                              "Welcome {name} to {chat}! Your username is {username}.")
        
        await send_welcome_message(update, self.context)
        
        # Verify message was sent with placeholders replaced
        self.context.bot.send_message.assert_called_once()
        args, kwargs = self.context.bot.send_message.call_args
        self.assertEqual(kwargs["chat_id"], self.group_chat.id)
        expected_text = f"Welcome {self.user.first_name} to {self.group_chat.title}! Your username is @{self.user.username}."
        self.assertEqual(kwargs["text"], expected_text)
    
    @pytest.mark.asyncio
    async def test_send_welcome_message_bot_joining(self):
        """Test welcome message is not sent when bot joins"""
        update = self.create_chat_member_update()
        
        # Set the new member as the bot itself
        update.chat_member.new_chat_member.user.id = self.context.bot.id
        
        await send_welcome_message(update, self.context)
        
        # Verify no message was sent
        self.context.bot.send_message.assert_not_called()
    
    def test_get_default_welcome_message(self):
        """Test default welcome message contains expected elements"""
        default_message = get_default_welcome_message()
        
        self.assertIn("Bienvenido a la familia", default_message)
        self.assertIn("{name}", default_message)
        self.assertIn("trabajamos duro", default_message)
        self.assertIn("/rules", default_message)


if __name__ == "__main__":
    unittest.main()