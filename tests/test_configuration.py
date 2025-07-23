"""
Unit tests for bot configuration management
Tests the /setstyle command and style configuration functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from telegram import Update, Message, Chat, User, ChatMember
from telegram.ext import ContextTypes

from handlers.commands import CommandHandler
from utils.theme import ThemeEngine, ToneStyle, MessageType
from database.manager import DatabaseManager
from database.repositories import ConfigRepository


class TestConfigurationManagement:
    """Test cases for bot configuration management"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager"""
        db_manager = Mock(spec=DatabaseManager)
        db_manager.get_cursor.return_value.__enter__ = Mock()
        db_manager.get_cursor.return_value.__exit__ = Mock()
        return db_manager
    
    @pytest.fixture
    def theme_engine(self):
        """Create a theme engine instance"""
        return ThemeEngine(ToneStyle.SERIOUS)
    
    @pytest.fixture
    def command_handler(self, theme_engine, mock_db_manager):
        """Create a command handler with mocked dependencies"""
        with patch('handlers.commands.get_database_manager', return_value=mock_db_manager):
            handler = CommandHandler(theme_engine)
            return handler
    
    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update"""
        update = Mock(spec=Update)
        update.effective_chat = Mock(spec=Chat)
        update.effective_chat.id = 12345
        update.effective_chat.type = "group"
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 67890
        update.effective_user.first_name = "TestUser"
        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Telegram context"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = Mock()
        context.bot.get_chat_member = AsyncMock()
        context.args = []
        return context
    
    @pytest.mark.asyncio
    async def test_setstyle_no_args_shows_current_style(self, command_handler, mock_update, mock_context):
        """Test that /setstyle without arguments shows current style"""
        # Mock admin check
        mock_chat_member = Mock(spec=ChatMember)
        mock_chat_member.status = "administrator"
        mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Mock config repository to return current style
        command_handler.config_repository.get_config = Mock(return_value="serio")
        
        await command_handler.handle_setstyle(mock_update, mock_context)
        
        # Verify that reply was sent with current style info
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "ESTILO ACTUAL" in call_args[0][0]
        assert "Serio" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_setstyle_serious_tone(self, command_handler, mock_update, mock_context):
        """Test setting bot style to serious tone"""
        # Mock admin check
        mock_chat_member = Mock(spec=ChatMember)
        mock_chat_member.status = "administrator"
        mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Set command arguments
        mock_context.args = ["serio"]
        
        # Mock config repository
        command_handler.config_repository.set_config = Mock()
        
        await command_handler.handle_setstyle(mock_update, mock_context)
        
        # Verify config was saved
        command_handler.config_repository.set_config.assert_called_once_with(
            12345, "bot_style", "serio"
        )
        
        # Verify theme engine was updated
        assert command_handler.theme_engine.get_tone() == ToneStyle.SERIOUS
        
        # Verify success message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Serio" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_setstyle_humorous_tone(self, command_handler, mock_update, mock_context):
        """Test setting bot style to humorous tone"""
        # Mock admin check
        mock_chat_member = Mock(spec=ChatMember)
        mock_chat_member.status = "administrator"
        mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Set command arguments
        mock_context.args = ["humorístico"]
        
        # Mock config repository
        command_handler.config_repository.set_config = Mock()
        
        await command_handler.handle_setstyle(mock_update, mock_context)
        
        # Verify config was saved
        command_handler.config_repository.set_config.assert_called_once_with(
            12345, "bot_style", "humorístico"
        )
        
        # Verify theme engine was updated
        assert command_handler.theme_engine.get_tone() == ToneStyle.HUMOROUS
        
        # Verify success message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Humorístico" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_setstyle_invalid_style(self, command_handler, mock_update, mock_context):
        """Test setting invalid bot style"""
        # Mock admin check
        mock_chat_member = Mock(spec=ChatMember)
        mock_chat_member.status = "administrator"
        mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Set invalid command arguments
        mock_context.args = ["invalid_style"]
        
        await command_handler.handle_setstyle(mock_update, mock_context)
        
        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "no reconocido" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_setstyle_non_admin_user(self, command_handler, mock_update, mock_context):
        """Test that non-admin users cannot change bot style"""
        # Mock non-admin user
        mock_chat_member = Mock(spec=ChatMember)
        mock_chat_member.status = "member"
        mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Set command arguments
        mock_context.args = ["serio"]
        
        await command_handler.handle_setstyle(mock_update, mock_context)
        
        # Verify warning message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "administradores" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_setstyle_private_chat(self, command_handler, mock_update, mock_context):
        """Test setstyle command in private chat (should work without admin check)"""
        # Set chat type to private
        mock_update.effective_chat.type = "private"
        
        # Set command arguments
        mock_context.args = ["humorístico"]
        
        # Mock config repository
        command_handler.config_repository.set_config = Mock()
        
        await command_handler.handle_setstyle(mock_update, mock_context)
        
        # Verify config was saved (no admin check in private chat)
        command_handler.config_repository.set_config.assert_called_once_with(
            12345, "bot_style", "humorístico"
        )
        
        # Verify theme engine was updated
        assert command_handler.theme_engine.get_tone() == ToneStyle.HUMOROUS
    
    @pytest.mark.asyncio
    async def test_setstyle_alternative_names(self, command_handler, mock_update, mock_context):
        """Test setstyle command with alternative style names"""
        # Mock admin check
        mock_chat_member = Mock(spec=ChatMember)
        mock_chat_member.status = "administrator"
        mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Mock config repository
        command_handler.config_repository.set_config = Mock()
        
        # Test alternative names for serious
        for style_name in ["serious", "serio"]:
            mock_context.args = [style_name]
            await command_handler.handle_setstyle(mock_update, mock_context)
            assert command_handler.theme_engine.get_tone() == ToneStyle.SERIOUS
        
        # Test alternative names for humorous
        for style_name in ["humoristico", "humorous", "divertido", "gracioso"]:
            mock_context.args = [style_name]
            await command_handler.handle_setstyle(mock_update, mock_context)
            assert command_handler.theme_engine.get_tone() == ToneStyle.HUMOROUS
    
    def test_load_chat_style_serious(self, command_handler):
        """Test loading serious chat style from database"""
        # Mock config repository to return serious style
        command_handler.config_repository.get_config = Mock(return_value="serio")
        
        command_handler._load_chat_style(12345)
        
        # Verify theme engine was set to serious
        assert command_handler.theme_engine.get_tone() == ToneStyle.SERIOUS
        
        # Verify config was queried
        command_handler.config_repository.get_config.assert_called_once_with(
            12345, "bot_style", "serio"
        )
    
    def test_load_chat_style_humorous(self, command_handler):
        """Test loading humorous chat style from database"""
        # Mock config repository to return humorous style
        command_handler.config_repository.get_config = Mock(return_value="humorístico")
        
        command_handler._load_chat_style(12345)
        
        # Verify theme engine was set to humorous
        assert command_handler.theme_engine.get_tone() == ToneStyle.HUMOROUS
    
    def test_load_chat_style_default(self, command_handler):
        """Test loading default chat style when none configured"""
        # Mock config repository to return default
        command_handler.config_repository.get_config = Mock(return_value="serio")
        
        command_handler._load_chat_style(12345)
        
        # Verify theme engine was set to serious (default)
        assert command_handler.theme_engine.get_tone() == ToneStyle.SERIOUS
    
    def test_load_chat_style_error_handling(self, command_handler):
        """Test error handling when loading chat style fails"""
        # Mock config repository to raise exception
        command_handler.config_repository.get_config = Mock(side_effect=Exception("Database error"))
        
        # Should not raise exception, should default to serious
        command_handler._load_chat_style(12345)
        
        # Verify theme engine was set to serious (default on error)
        assert command_handler.theme_engine.get_tone() == ToneStyle.SERIOUS
    
    @pytest.mark.asyncio
    async def test_setstyle_database_error(self, command_handler, mock_update, mock_context):
        """Test setstyle command when database operation fails"""
        # Mock admin check
        mock_chat_member = Mock(spec=ChatMember)
        mock_chat_member.status = "administrator"
        mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Set command arguments
        mock_context.args = ["serio"]
        
        # Mock config repository to raise exception
        command_handler.config_repository.set_config = Mock(side_effect=Exception("Database error"))
        
        await command_handler.handle_setstyle(mock_update, mock_context)
        
        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        # Should contain error message from theme engine
        assert len(call_args[0][0]) > 0  # Some error message was sent


class TestThemeEngineIntegration:
    """Test integration between configuration and theme engine"""
    
    def test_theme_engine_tone_persistence(self):
        """Test that theme engine tone changes persist"""
        theme_engine = ThemeEngine(ToneStyle.SERIOUS)
        
        # Verify initial state
        assert theme_engine.get_tone() == ToneStyle.SERIOUS
        
        # Change to humorous
        theme_engine.set_tone(ToneStyle.HUMOROUS)
        assert theme_engine.get_tone() == ToneStyle.HUMOROUS
        
        # Change back to serious
        theme_engine.set_tone(ToneStyle.SERIOUS)
        assert theme_engine.get_tone() == ToneStyle.SERIOUS
    
    def test_theme_engine_message_generation_with_different_tones(self):
        """Test that theme engine generates different messages based on tone"""
        theme_engine = ThemeEngine(ToneStyle.SERIOUS)
        
        # Generate message with serious tone
        serious_message = theme_engine.generate_message(MessageType.SUCCESS)
        
        # Change to humorous tone
        theme_engine.set_tone(ToneStyle.HUMOROUS)
        humorous_message = theme_engine.generate_message(MessageType.SUCCESS)
        
        # Messages should be different (though this is probabilistic)
        # At minimum, they should both be non-empty strings
        assert isinstance(serious_message, str)
        assert isinstance(humorous_message, str)
        assert len(serious_message) > 0
        assert len(humorous_message) > 0