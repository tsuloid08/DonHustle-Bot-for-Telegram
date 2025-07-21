"""
Unit tests for basic command handlers
"""

import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from telegram import Update, User, Chat, Message, ChatMember
from telegram.ext import ContextTypes

from handlers.commands import CommandHandler, BaseCommandHandler
from utils.theme import ThemeEngine, MessageType, ToneStyle
from database.manager import DatabaseManager


class TestCommandHandler(unittest.TestCase):
    """Test cases for basic command handlers"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock database manager
        self.db_manager_patcher = patch('handlers.commands.get_database_manager')
        self.mock_db_manager = self.db_manager_patcher.start()
        
        # Create mock cursor and connection
        self.mock_cursor = MagicMock()
        self.mock_db_manager.return_value.get_cursor.return_value.__enter__.return_value = self.mock_cursor
        
        # Set up theme engine and command handler
        self.theme_engine = ThemeEngine()
        self.command_handler = CommandHandler(self.theme_engine)
        
        # Mock user and chat
        self.user = MagicMock(spec=User)
        self.user.first_name = "TestUser"
        self.user.id = 123456789
        
        # Mock private chat
        self.private_chat = MagicMock(spec=Chat)
        self.private_chat.id = 123456789
        self.private_chat.type = "private"
        
        # Mock group chat
        self.group_chat = MagicMock(spec=Chat)
        self.group_chat.id = 987654321
        self.group_chat.type = "group"
        
        # Mock context
        self.context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        self.context.bot = MagicMock()
        self.context.bot.get_chat_member = AsyncMock()
    
    def tearDown(self):
        """Clean up after tests"""
        self.db_manager_patcher.stop()
    
    def create_mock_update(self, chat_type="private"):
        """Create a mock update with specified chat type"""
        update = MagicMock(spec=Update)
        update.effective_user = self.user
        
        if chat_type == "private":
            update.effective_chat = self.private_chat
        else:
            update.effective_chat = self.group_chat
        
        # Mock message
        message = MagicMock(spec=Message)
        message.reply_text = AsyncMock()
        update.message = message
        update.effective_message = message
        
        return update
    
    @pytest.mark.asyncio
    async def test_handle_start_private(self):
        """Test /start command in private chat"""
        update = self.create_mock_update(chat_type="private")
        
        await self.command_handler.handle_start(update, self.context)
        
        # Verify reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the welcome message contains the user's name
        args, kwargs = update.message.reply_text.call_args
        self.assertIn(self.user.first_name, args[0])
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")
    
    @pytest.mark.asyncio
    async def test_handle_start_group(self):
        """Test /start command in group chat"""
        update = self.create_mock_update(chat_type="group")
        
        await self.command_handler.handle_start(update, self.context)
        
        # Verify reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the welcome message contains the user's name
        args, kwargs = update.message.reply_text.call_args
        self.assertIn(self.user.first_name, args[0])
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")
    
    @pytest.mark.asyncio
    async def test_handle_rules_default(self):
        """Test /rules command with default rules"""
        update = self.create_mock_update()
        
        # Mock database query to return no custom rules
        self.mock_cursor.fetchone.return_value = None
        
        await self.command_handler.handle_rules(update, self.context)
        
        # Verify reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the rules message contains expected content
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("REGLAS DE LA FAMILIA", args[0])
        self.assertIn("Trabaja duro", args[0])
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")
    
    @pytest.mark.asyncio
    async def test_handle_rules_custom(self):
        """Test /rules command with custom rules from database"""
        update = self.create_mock_update()
        
        # Mock database query to return custom rules
        self.mock_cursor.fetchone.return_value = ["Regla personalizada 1\nRegla personalizada 2"]
        
        await self.command_handler.handle_rules(update, self.context)
        
        # Verify reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the rules message contains expected content
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("REGLAS DE LA FAMILIA", args[0])
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")
    
    @pytest.mark.asyncio
    async def test_handle_help_private(self):
        """Test /help command in private chat"""
        update = self.create_mock_update(chat_type="private")
        
        await self.command_handler.handle_help(update, self.context)
        
        # Verify reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the help message contains expected commands
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("/start", args[0])
        self.assertIn("/rules", args[0])
        self.assertIn("/help", args[0])
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")
    
    @pytest.mark.asyncio
    async def test_handle_help_group_regular_user(self):
        """Test /help command in group chat for regular user"""
        update = self.create_mock_update(chat_type="group")
        
        # Mock chat member status as regular member
        mock_chat_member = MagicMock(spec=ChatMember)
        mock_chat_member.status = "member"
        self.context.bot.get_chat_member.return_value = mock_chat_member
        
        await self.command_handler.handle_help(update, self.context)
        
        # Verify reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the help message contains expected commands but not admin commands
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("/rules", args[0])
        self.assertIn("/hustle", args[0])
        self.assertNotIn("/welcome", args[0])  # Admin command should not be included
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")
    
    @pytest.mark.asyncio
    async def test_handle_help_group_admin(self):
        """Test /help command in group chat for admin user"""
        update = self.create_mock_update(chat_type="group")
        
        # Mock chat member status as admin
        mock_chat_member = MagicMock(spec=ChatMember)
        mock_chat_member.status = "administrator"
        self.context.bot.get_chat_member.return_value = mock_chat_member
        
        await self.command_handler.handle_help(update, self.context)
        
        # Verify reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the help message contains both regular and admin commands
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("/rules", args[0])
        self.assertIn("/hustle", args[0])
        self.assertIn("/welcome", args[0])  # Admin command should be included
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")
    
    @pytest.mark.asyncio
    async def test_handle_hustle_no_quotes(self):
        """Test /hustle command when no quotes in database"""
        update = self.create_mock_update()
        
        # Mock database query to return no quotes
        self.mock_cursor.fetchone.return_value = None
        
        await self.command_handler.handle_hustle(update, self.context)
        
        # Verify reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that a default quote was used
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("*", args[0])  # Should contain formatted quote
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")
    
    @pytest.mark.asyncio
    async def test_handle_hustle_with_quote(self):
        """Test /hustle command with quote from database"""
        update = self.create_mock_update()
        
        # Mock database query to return a quote
        self.mock_cursor.fetchone.return_value = ["El éxito es la suma de pequeños esfuerzos repetidos día tras día."]
        
        await self.command_handler.handle_hustle(update, self.context)
        
        # Verify reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the database quote was used
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("*", args[0])  # Should contain formatted quote
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")
    
    def test_command_registration(self):
        """Test command registration system"""
        # Register a test command
        test_handler = AsyncMock()
        self.command_handler.register_command("test", test_handler)
        
        # Verify command was registered
        commands = self.command_handler.get_registered_commands()
        self.assertIn("test", commands)
        self.assertEqual(commands["test"], test_handler)


class TestBaseCommandHandler(unittest.TestCase):
    """Test cases for the abstract BaseCommandHandler class"""
    
    def test_get_command_name(self):
        """Test command name extraction from class name"""
        # Create a concrete implementation of the abstract class for testing
        class TestCommand(BaseCommandHandler):
            async def handle(self, update, context):
                pass
        
        # Create instance with mock theme engine
        theme_engine = MagicMock(spec=ThemeEngine)
        handler = TestCommand(theme_engine)
        
        # Test command name extraction
        self.assertEqual(handler.get_command_name(), "test")
        
        # Test with different class name format
        class AnotherTestCommand(BaseCommandHandler):
            async def handle(self, update, context):
                pass
        
        handler = AnotherTestCommand(theme_engine)
        self.assertEqual(handler.get_command_name(), "anothertest")


if __name__ == "__main__":
    unittest.main()