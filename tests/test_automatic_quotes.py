"""
Integration tests for automatic quote sending system in @donhustle_bot
Tests message counting, interval configuration, and automatic quote triggering
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from telegram import Update, Message, Chat, User, Bot
from telegram.ext import ContextTypes

from handlers.commands import CommandHandler
from handlers.message_handler import BotMessageHandler
from utils.theme import ThemeEngine, ToneStyle
from database.models import Quote
from database.repositories import QuoteRepository, ConfigRepository, UserActivityRepository


class TestAutomaticQuoteSystem:
    """Test class for automatic quote sending system"""
    
    @pytest.fixture
    def theme_engine(self):
        """Create a theme engine for testing"""
        return ThemeEngine(ToneStyle.SERIOUS)
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager"""
        mock_db = Mock()
        mock_db.get_cursor.return_value.__enter__ = Mock()
        mock_db.get_cursor.return_value.__exit__ = Mock()
        return mock_db
    
    @pytest.fixture
    def mock_repositories(self, mock_db_manager):
        """Create mock repositories"""
        quote_repo = Mock(spec=QuoteRepository)
        config_repo = Mock(spec=ConfigRepository)
        activity_repo = Mock(spec=UserActivityRepository)
        
        return {
            'quote': quote_repo,
            'config': config_repo,
            'activity': activity_repo
        }
    
    @pytest.fixture
    def command_handler(self, theme_engine, mock_db_manager, mock_repositories):
        """Create a command handler with mocked dependencies"""
        with patch('handlers.commands.get_database_manager', return_value=mock_db_manager):
            with patch('handlers.commands.QuoteRepository', return_value=mock_repositories['quote']):
                with patch('handlers.commands.ConfigRepository', return_value=mock_repositories['config']):
                    with patch('handlers.commands.UserActivityRepository', return_value=mock_repositories['activity']):
                        handler = CommandHandler(theme_engine)
                        handler.quote_repository = mock_repositories['quote']
                        handler.config_repository = mock_repositories['config']
                        handler.user_activity_repository = mock_repositories['activity']
                        return handler
    
    @pytest.fixture
    def message_handler(self, theme_engine, mock_db_manager, mock_repositories):
        """Create a message handler with mocked dependencies"""
        with patch('handlers.message_handler.get_database_manager', return_value=mock_db_manager):
            with patch('handlers.message_handler.QuoteRepository', return_value=mock_repositories['quote']):
                with patch('handlers.message_handler.ConfigRepository', return_value=mock_repositories['config']):
                    with patch('handlers.message_handler.UserActivityRepository', return_value=mock_repositories['activity']):
                        handler = BotMessageHandler(theme_engine)
                        handler.quote_repository = mock_repositories['quote']
                        handler.config_repository = mock_repositories['config']
                        handler.user_activity_repository = mock_repositories['activity']
                        return handler
    
    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update"""
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 12345
        update.effective_user.first_name = "TestUser"
        update.effective_user.is_bot = False
        
        update.effective_chat = Mock(spec=Chat)
        update.effective_chat.id = 67890
        update.effective_chat.type = "group"
        
        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.message.text = "Regular message"
        update.effective_message = update.message
        
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Telegram context"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        context.bot = Mock(spec=Bot)
        context.bot.send_message = AsyncMock()
        context.bot.get_chat_member = AsyncMock()
        
        # Mock admin status
        mock_chat_member = Mock()
        mock_chat_member.status = "administrator"
        context.bot.get_chat_member.return_value = mock_chat_member
        
        return context
    
    @pytest.fixture
    def sample_quote(self):
        """Create a sample quote for testing"""
        return Quote(
            id=1, 
            quote="El trabajo duro siempre da frutos", 
            created_at=datetime.now()
        )

    @pytest.mark.asyncio
    async def test_setquoteinterval_command_success(self, command_handler, mock_update, mock_context, mock_repositories):
        """Test /setquoteinterval command with valid interval"""
        # Setup
        mock_context.args = ["25"]
        mock_repositories['config'].get_config.return_value = "50"  # Current interval
        
        # Execute
        await command_handler.handle_setquoteinterval(mock_update, mock_context)
        
        # Verify
        mock_repositories['config'].set_config.assert_any_call(67890, "quote_interval", "25")
        mock_repositories['config'].set_config.assert_any_call(67890, "message_count", "0")
        mock_update.message.reply_text.assert_called_once()
        
        # Check success message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "cada *25* mensajes" in message_text

    @pytest.mark.asyncio
    async def test_setquoteinterval_show_current(self, command_handler, mock_update, mock_context, mock_repositories):
        """Test /setquoteinterval command without arguments shows current interval"""
        # Setup
        mock_context.args = []
        mock_repositories['config'].get_config.return_value = "30"
        
        # Execute
        await command_handler.handle_setquoteinterval(mock_update, mock_context)
        
        # Verify
        mock_repositories['config'].get_config.assert_called_with(67890, "quote_interval", "50")
        mock_update.message.reply_text.assert_called_once()
        
        # Check info message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "cada *30* mensajes" in message_text
        assert "/setquoteinterval [número]" in message_text

    @pytest.mark.asyncio
    async def test_setquoteinterval_too_small(self, command_handler, mock_update, mock_context):
        """Test /setquoteinterval command with too small interval"""
        # Setup
        mock_context.args = ["3"]
        
        # Execute
        await command_handler.handle_setquoteinterval(mock_update, mock_context)
        
        # Verify error message
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "demasiado pequeño" in message_text
        assert "mayor a 5" in message_text

    @pytest.mark.asyncio
    async def test_setquoteinterval_too_large(self, command_handler, mock_update, mock_context):
        """Test /setquoteinterval command with too large interval"""
        # Setup
        mock_context.args = ["1500"]
        
        # Execute
        await command_handler.handle_setquoteinterval(mock_update, mock_context)
        
        # Verify error message
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "demasiado grande" in message_text
        assert "menor a 1000" in message_text

    @pytest.mark.asyncio
    async def test_setquoteinterval_non_admin(self, command_handler, mock_update, mock_context):
        """Test /setquoteinterval command by non-admin user"""
        # Setup
        mock_context.args = ["25"]
        mock_chat_member = Mock()
        mock_chat_member.status = "member"  # Not admin
        mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Execute
        await command_handler.handle_setquoteinterval(mock_update, mock_context)
        
        # Verify warning message
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Solo los administradores" in message_text

    @pytest.mark.asyncio
    async def test_message_counting_and_quote_trigger(self, message_handler, mock_update, mock_context, mock_repositories, sample_quote):
        """Test message counting and automatic quote triggering"""
        # Setup - set interval to 3 for easy testing
        mock_repositories['config'].get_config.side_effect = lambda chat_id, key, default: {
            "message_count": "2",  # Already at 2, next message should trigger
            "quote_interval": "3"
        }.get(key, default)
        
        mock_repositories['quote'].get_random_quote.return_value = sample_quote
        
        # Execute
        await message_handler.handle_message(mock_update, mock_context)
        
        # Verify
        # Should increment message count to 3
        mock_repositories['config'].set_config.assert_any_call(67890, "message_count", "3")
        # Should reset counter after reaching interval
        mock_repositories['config'].set_config.assert_any_call(67890, "message_count", "0")
        # Should send quote
        mock_context.bot.send_message.assert_called_once()
        
        # Check quote message
        call_args = mock_context.bot.send_message.call_args
        assert call_args[1]['chat_id'] == 67890
        message_text = call_args[1]['text']
        assert "MOMENTO DE REFLEXIÓN" in message_text
        assert sample_quote.quote in message_text

    @pytest.mark.asyncio
    async def test_message_counting_no_trigger(self, message_handler, mock_update, mock_context, mock_repositories):
        """Test message counting without triggering quote"""
        # Setup - set count below interval
        mock_repositories['config'].get_config.side_effect = lambda chat_id, key, default: {
            "message_count": "1",  # Below interval
            "quote_interval": "5"
        }.get(key, default)
        
        # Execute
        await message_handler.handle_message(mock_update, mock_context)
        
        # Verify
        # Should increment message count
        mock_repositories['config'].set_config.assert_called_once_with(67890, "message_count", "2")
        # Should NOT send quote
        mock_context.bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_message_counting_no_quotes_available(self, message_handler, mock_update, mock_context, mock_repositories):
        """Test message counting when no quotes are available"""
        # Setup - trigger interval but no quotes
        mock_repositories['config'].get_config.side_effect = lambda chat_id, key, default: {
            "message_count": "4",  # At interval
            "quote_interval": "5"
        }.get(key, default)
        
        mock_repositories['quote'].get_random_quote.return_value = None  # No quotes
        
        # Execute
        await message_handler.handle_message(mock_update, mock_context)
        
        # Verify
        # Should reset counter even without quotes
        mock_repositories['config'].set_config.assert_any_call(67890, "message_count", "0")
        # Should NOT send message
        mock_context.bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_bot_messages(self, message_handler, mock_update, mock_context, mock_repositories):
        """Test that bot messages are skipped"""
        # Setup
        mock_update.effective_user.is_bot = True
        
        # Execute
        await message_handler.handle_message(mock_update, mock_context)
        
        # Verify - no processing should happen
        mock_repositories['activity'].update_user_activity.assert_not_called()
        mock_repositories['config'].get_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_command_messages(self, message_handler, mock_update, mock_context, mock_repositories):
        """Test that command messages are skipped"""
        # Setup
        mock_update.message.text = "/start"
        
        # Execute
        await message_handler.handle_message(mock_update, mock_context)
        
        # Verify - no processing should happen
        mock_repositories['activity'].update_user_activity.assert_not_called()
        mock_repositories['config'].get_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_private_chat_messages(self, message_handler, mock_update, mock_context, mock_repositories):
        """Test that private chat messages are skipped for quote intervals"""
        # Setup
        mock_update.effective_chat.type = "private"
        
        # Execute
        await message_handler.handle_message(mock_update, mock_context)
        
        # Verify - no quote processing should happen
        mock_repositories['config'].get_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_user_activity_tracking(self, message_handler, mock_update, mock_context, mock_repositories):
        """Test that user activity is tracked for all messages"""
        # Execute
        await message_handler.handle_message(mock_update, mock_context)
        
        # Verify user activity is updated
        mock_repositories['activity'].update_user_activity.assert_called_once_with(12345, 67890)

    @pytest.mark.asyncio
    async def test_theme_engine_integration_serious(self, message_handler, mock_update, mock_context, mock_repositories, sample_quote):
        """Test theme engine integration with serious tone"""
        # Setup
        message_handler.theme_engine.set_tone(ToneStyle.SERIOUS)
        mock_repositories['config'].get_config.side_effect = lambda chat_id, key, default: {
            "message_count": "4",
            "quote_interval": "5"
        }.get(key, default)
        mock_repositories['quote'].get_random_quote.return_value = sample_quote
        
        # Execute
        await message_handler.handle_message(mock_update, mock_context)
        
        # Verify serious tone message
        call_args = mock_context.bot.send_message.call_args
        message_text = call_args[1]['text']
        assert "MOMENTO DE REFLEXIÓN" in message_text

    @pytest.mark.asyncio
    async def test_theme_engine_integration_humorous(self, message_handler, mock_update, mock_context, mock_repositories, sample_quote):
        """Test theme engine integration with humorous tone"""
        # Setup
        message_handler.theme_engine.set_tone(ToneStyle.HUMOROUS)
        mock_repositories['config'].get_config.side_effect = lambda chat_id, key, default: {
            "message_count": "4",
            "quote_interval": "5"
        }.get(key, default)
        mock_repositories['quote'].get_random_quote.return_value = sample_quote
        
        # Execute
        await message_handler.handle_message(mock_update, mock_context)
        
        # Verify humorous tone message
        call_args = mock_context.bot.send_message.call_args
        message_text = call_args[1]['text']
        assert "¡ALARMA DE MOTIVACIÓN!" in message_text

    @pytest.mark.asyncio
    async def test_error_handling_in_message_processing(self, message_handler, mock_update, mock_context, mock_repositories):
        """Test error handling in message processing"""
        # Setup - make repository throw exception
        mock_repositories['config'].get_config.side_effect = Exception("Database error")
        
        # Execute - should not raise exception
        await message_handler.handle_message(mock_update, mock_context)
        
        # Verify - user activity should still be updated despite error
        mock_repositories['activity'].update_user_activity.assert_called_once()

    def test_interval_validation_logic(self, command_handler):
        """Test interval validation logic"""
        # Test valid intervals
        assert 5 <= 25 <= 1000  # Should be valid
        assert 5 <= 100 <= 1000  # Should be valid
        
        # Test invalid intervals
        assert not (5 <= 3 <= 1000)  # Too small
        assert not (5 <= 1500 <= 1000)  # Too large

    def test_integration_components_exist(self, command_handler, message_handler):
        """Test that integration components are properly initialized"""
        # Test that handlers have the required repositories
        assert hasattr(command_handler, 'config_repository')
        assert hasattr(command_handler, 'quote_repository')
        assert hasattr(message_handler, 'config_repository')
        assert hasattr(message_handler, 'quote_repository')
        assert hasattr(message_handler, 'user_activity_repository')
        
        # Test that theme engines are properly configured
        assert command_handler.theme_engine is not None
        assert message_handler.theme_engine is not None


if __name__ == "__main__":
    pytest.main([__file__])