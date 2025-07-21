"""
Unit tests for message saving functionality in @donhustle_bot
Tests the /save and /savedmessages commands
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from telegram import Update, Message, Chat, User
from telegram.ext import ContextTypes

from handlers.commands import CommandHandler
from utils.theme import ThemeEngine, ToneStyle
from database.models import SavedMessage


class TestMessageSaving:
    """Test cases for message saving functionality"""
    
    @pytest.fixture
    def theme_engine(self):
        """Create a theme engine for testing"""
        return ThemeEngine(ToneStyle.SERIOUS)
    
    @pytest.fixture
    def command_handler(self, theme_engine):
        """Create a command handler with mocked dependencies"""
        with patch('handlers.commands.get_database_manager'):
            handler = CommandHandler(theme_engine)
            handler.message_repository = Mock()
            return handler
    
    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update object"""
        update = Mock(spec=Update)
        update.effective_chat = Mock(spec=Chat)
        update.effective_chat.id = 12345
        update.effective_chat.type = "group"
        
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 67890
        update.effective_user.first_name = "TestUser"
        
        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.message.message_id = 999
        
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Telegram context object"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        return context
    
    @pytest.mark.asyncio
    async def test_save_command_no_reply_no_args(self, command_handler, mock_update, mock_context):
        """Test /save command without reply message and without arguments"""
        # Setup
        mock_context.args = []
        mock_update.message.reply_to_message = None
        
        # Execute
        await command_handler.handle_save(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "No especificaste qué guardar" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "Markdown"
    
    @pytest.mark.asyncio
    async def test_save_command_reply_to_text_message(self, command_handler, mock_update, mock_context):
        """Test /save command replying to a text message"""
        # Setup
        mock_context.args = []
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = "This is an important message to save"
        mock_update.message.reply_to_message.caption = None
        mock_update.message.reply_to_message.message_id = 123
        
        command_handler.message_repository.save_message.return_value = 1
        
        # Execute
        await command_handler.handle_save(mock_update, mock_context)
        
        # Verify repository call
        command_handler.message_repository.save_message.assert_called_once_with(
            chat_id=12345,
            message_id=123,
            content="This is an important message to save",
            saved_by=67890,
            tag=None
        )
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Mensaje guardado en los archivos importantes" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_save_command_reply_to_media_message(self, command_handler, mock_update, mock_context):
        """Test /save command replying to a media message with caption"""
        # Setup
        mock_context.args = []
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = None
        mock_update.message.reply_to_message.caption = "Important photo caption"
        mock_update.message.reply_to_message.message_id = 123
        
        command_handler.message_repository.save_message.return_value = 1
        
        # Execute
        await command_handler.handle_save(mock_update, mock_context)
        
        # Verify repository call
        command_handler.message_repository.save_message.assert_called_once_with(
            chat_id=12345,
            message_id=123,
            content="Important photo caption",
            saved_by=67890,
            tag=None
        )
    
    @pytest.mark.asyncio
    async def test_save_command_reply_to_multimedia_no_text(self, command_handler, mock_update, mock_context):
        """Test /save command replying to multimedia message without text or caption"""
        # Setup
        mock_context.args = []
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = None
        mock_update.message.reply_to_message.caption = None
        mock_update.message.reply_to_message.message_id = 123
        
        command_handler.message_repository.save_message.return_value = 1
        
        # Execute
        await command_handler.handle_save(mock_update, mock_context)
        
        # Verify repository call
        command_handler.message_repository.save_message.assert_called_once_with(
            chat_id=12345,
            message_id=123,
            content="[Mensaje multimedia]",
            saved_by=67890,
            tag=None
        )
    
    @pytest.mark.asyncio
    async def test_save_command_with_text_arguments(self, command_handler, mock_update, mock_context):
        """Test /save command with text arguments"""
        # Setup
        mock_context.args = ["This", "is", "important", "text", "to", "save"]
        mock_update.message.reply_to_message = None
        
        command_handler.message_repository.save_message.return_value = 1
        
        # Execute
        await command_handler.handle_save(mock_update, mock_context)
        
        # Verify repository call
        command_handler.message_repository.save_message.assert_called_once_with(
            chat_id=12345,
            message_id=999,
            content="This is important text to save",
            saved_by=67890,
            tag=None
        )
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Texto guardado en los archivos importantes" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_save_command_text_too_short(self, command_handler, mock_update, mock_context):
        """Test /save command with text that's too short"""
        # Setup
        mock_context.args = ["Hi"]
        mock_update.message.reply_to_message = None
        
        # Execute
        await command_handler.handle_save(mock_update, mock_context)
        
        # Verify error response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "El mensaje es demasiado corto" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_save_command_text_too_long(self, command_handler, mock_update, mock_context):
        """Test /save command with text that's too long"""
        # Setup - create text that exceeds 1000 characters
        long_word = "A" * 100  # 100 character word
        long_text = [long_word] * 12  # 12 words of 100 chars each = 1200+ chars when joined
        mock_context.args = long_text
        mock_update.message.reply_to_message = None
        
        # Execute
        await command_handler.handle_save(mock_update, mock_context)
        
        # Verify error response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "El mensaje es demasiado largo" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_save_command_database_error_reply(self, command_handler, mock_update, mock_context):
        """Test /save command when database save fails for reply message"""
        # Setup
        mock_context.args = []
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = "Test message"
        mock_update.message.reply_to_message.message_id = 123
        
        command_handler.message_repository.save_message.return_value = None
        
        # Execute
        await command_handler.handle_save(mock_update, mock_context)
        
        # Verify error response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "No se pudo guardar el mensaje" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_save_command_database_error_text(self, command_handler, mock_update, mock_context):
        """Test /save command when database save fails for text arguments"""
        # Setup
        mock_context.args = ["Important", "text", "to", "save"]
        mock_update.message.reply_to_message = None
        
        command_handler.message_repository.save_message.return_value = None
        
        # Execute
        await command_handler.handle_save(mock_update, mock_context)
        
        # Verify error response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "No se pudo guardar el texto" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_savedmessages_command_no_messages(self, command_handler, mock_update, mock_context):
        """Test /savedmessages command when no messages are saved"""
        # Setup
        command_handler.message_repository.get_saved_messages.return_value = []
        
        # Execute
        await command_handler.handle_savedmessages(mock_update, mock_context)
        
        # Verify repository call
        command_handler.message_repository.get_saved_messages.assert_called_once_with(12345)
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "No hay mensajes guardados" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_savedmessages_command_single_message(self, command_handler, mock_update, mock_context):
        """Test /savedmessages command with single saved message"""
        # Setup
        test_message = SavedMessage(
            id=1,
            chat_id=12345,
            message_id=123,
            content="This is a saved message",
            tag=None,  # No tag for saved messages
            saved_by=67890,
            created_at=datetime(2024, 1, 15, 10, 30)
        )
        
        command_handler.message_repository.get_saved_messages.return_value = [test_message]
        
        # Execute
        await command_handler.handle_savedmessages(mock_update, mock_context)
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "MENSAJES IMPORTANTES DE LA FAMILIA" in response_text
        assert "15/01/2024 10:30" in response_text
        assert "This is a saved message" in response_text
        assert "Total: 1 mensajes importantes" in response_text
    
    @pytest.mark.asyncio
    async def test_savedmessages_command_multiple_messages(self, command_handler, mock_update, mock_context):
        """Test /savedmessages command with multiple saved messages"""
        # Setup
        test_messages = [
            SavedMessage(
                id=1,
                chat_id=12345,
                message_id=123,
                content="First saved message",
                tag=None,
                saved_by=67890,
                created_at=datetime(2024, 1, 15, 10, 30)
            ),
            SavedMessage(
                id=2,
                chat_id=12345,
                message_id=124,
                content="Second saved message",
                tag=None,
                saved_by=67890,
                created_at=datetime(2024, 1, 16, 11, 45)
            )
        ]
        
        command_handler.message_repository.get_saved_messages.return_value = test_messages
        
        # Execute
        await command_handler.handle_savedmessages(mock_update, mock_context)
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "MENSAJES IMPORTANTES DE LA FAMILIA" in response_text
        assert "First saved message" in response_text
        assert "Second saved message" in response_text
        assert "Total: 2 mensajes importantes" in response_text
    
    @pytest.mark.asyncio
    async def test_savedmessages_command_filters_tagged_messages(self, command_handler, mock_update, mock_context):
        """Test /savedmessages command filters out tagged messages"""
        # Setup - mix of saved messages (no tag) and tagged messages
        all_messages = [
            SavedMessage(
                id=1,
                chat_id=12345,
                message_id=123,
                content="Saved message without tag",
                tag=None,  # This should be included
                saved_by=67890,
                created_at=datetime(2024, 1, 15, 10, 30)
            ),
            SavedMessage(
                id=2,
                chat_id=12345,
                message_id=124,
                content="Tagged message",
                tag="important",  # This should be filtered out
                saved_by=67890,
                created_at=datetime(2024, 1, 16, 11, 45)
            )
        ]
        
        command_handler.message_repository.get_saved_messages.return_value = all_messages
        
        # Execute
        await command_handler.handle_savedmessages(mock_update, mock_context)
        
        # Verify response only includes non-tagged messages
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "Saved message without tag" in response_text
        assert "Tagged message" not in response_text
        assert "Total: 1 mensajes importantes" in response_text
    
    @pytest.mark.asyncio
    async def test_savedmessages_command_long_message_truncation(self, command_handler, mock_update, mock_context):
        """Test /savedmessages command truncates long messages"""
        # Setup
        long_content = "A" * 200  # 200 characters, should be truncated
        test_message = SavedMessage(
            id=1,
            chat_id=12345,
            message_id=123,
            content=long_content,
            tag=None,
            saved_by=67890,
            created_at=datetime(2024, 1, 15, 10, 30)
        )
        
        command_handler.message_repository.get_saved_messages.return_value = [test_message]
        
        # Execute
        await command_handler.handle_savedmessages(mock_update, mock_context)
        
        # Verify response contains truncated content
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "A" * 147 + "..." in response_text  # Should be truncated to 147 chars + "..."
    
    @pytest.mark.asyncio
    async def test_savedmessages_command_database_error(self, command_handler, mock_update, mock_context):
        """Test /savedmessages command when database query fails"""
        # Setup
        command_handler.message_repository.get_saved_messages.side_effect = Exception("Database error")
        
        # Execute
        await command_handler.handle_savedmessages(mock_update, mock_context)
        
        # Verify error response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        # Should contain error message from theme engine
        assert call_args[1]["parse_mode"] == "Markdown"
    
    @pytest.mark.asyncio
    async def test_save_command_humorous_tone(self, mock_update, mock_context):
        """Test /save command with humorous tone"""
        # Setup with humorous theme
        theme_engine = ThemeEngine(ToneStyle.HUMOROUS)
        with patch('handlers.commands.get_database_manager'):
            handler = CommandHandler(theme_engine)
            handler.message_repository = Mock()
        
        mock_context.args = ["Funny", "text", "to", "save"]
        mock_update.message.reply_to_message = None
        
        handler.message_repository.save_message.return_value = 1
        
        # Execute
        await handler.handle_save(mock_update, mock_context)
        
        # Verify response contains humorous language
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "negocios importantes" in response_text
    
    @pytest.mark.asyncio
    async def test_savedmessages_command_humorous_tone(self, mock_update, mock_context):
        """Test /savedmessages command with humorous tone"""
        # Setup with humorous theme
        theme_engine = ThemeEngine(ToneStyle.HUMOROUS)
        with patch('handlers.commands.get_database_manager'):
            handler = CommandHandler(theme_engine)
            handler.message_repository = Mock()
        
        handler.message_repository.get_saved_messages.return_value = []
        
        # Execute
        await handler.handle_savedmessages(mock_update, mock_context)
        
        # Verify response contains humorous language
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "negocios importantes" in response_text
    
    @pytest.mark.asyncio
    async def test_save_command_exception_handling(self, command_handler, mock_update, mock_context):
        """Test /save command handles exceptions gracefully"""
        # Setup
        mock_context.args = []
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = "Test message"
        mock_update.message.reply_to_message.message_id = 123
        
        command_handler.message_repository.save_message.side_effect = Exception("Database error")
        
        # Execute
        await command_handler.handle_save(mock_update, mock_context)
        
        # Verify error response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        # Should contain error message from theme engine
        assert call_args[1]["parse_mode"] == "Markdown"