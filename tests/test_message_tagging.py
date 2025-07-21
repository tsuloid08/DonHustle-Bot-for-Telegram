"""
Unit tests for message tagging functionality in @donhustle_bot
Tests the /tag and /searchtag commands
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


class TestMessageTagging:
    """Test cases for message tagging functionality"""
    
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
        
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Telegram context object"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        return context
    
    @pytest.mark.asyncio
    async def test_tag_command_no_arguments(self, command_handler, mock_update, mock_context):
        """Test /tag command without arguments"""
        # Setup
        mock_context.args = []
        
        # Execute
        await command_handler.handle_tag(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "No especificaste la etiqueta" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "Markdown"
    
    @pytest.mark.asyncio
    async def test_tag_command_no_reply_message(self, command_handler, mock_update, mock_context):
        """Test /tag command without replying to a message"""
        # Setup
        mock_context.args = ["important"]
        mock_update.message.reply_to_message = None
        
        # Execute
        await command_handler.handle_tag(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Debes responder a un mensaje para etiquetarlo" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_tag_command_tag_too_short(self, command_handler, mock_update, mock_context):
        """Test /tag command with tag that's too short"""
        # Setup
        mock_context.args = ["a"]
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = "Test message"
        mock_update.message.reply_to_message.message_id = 123
        
        # Execute
        await command_handler.handle_tag(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "La etiqueta es demasiado corta" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_tag_command_tag_too_long(self, command_handler, mock_update, mock_context):
        """Test /tag command with tag that's too long"""
        # Setup
        long_tag = "a" * 51  # 51 characters, exceeds limit of 50
        mock_context.args = [long_tag]
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = "Test message"
        mock_update.message.reply_to_message.message_id = 123
        
        # Execute
        await command_handler.handle_tag(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "La etiqueta es demasiado larga" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_tag_command_successful_text_message(self, command_handler, mock_update, mock_context):
        """Test successful tagging of a text message"""
        # Setup
        mock_context.args = ["important"]
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = "This is an important message"
        mock_update.message.reply_to_message.caption = None
        mock_update.message.reply_to_message.message_id = 123
        
        command_handler.message_repository.save_message.return_value = 1
        
        # Execute
        await command_handler.handle_tag(mock_update, mock_context)
        
        # Verify repository call
        command_handler.message_repository.save_message.assert_called_once_with(
            chat_id=12345,
            message_id=123,
            content="This is an important message",
            saved_by=67890,
            tag="important"
        )
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Mensaje etiquetado como" in call_args[0][0]
        assert "important" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_tag_command_successful_media_message(self, command_handler, mock_update, mock_context):
        """Test successful tagging of a media message with caption"""
        # Setup
        mock_context.args = ["media"]
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = None
        mock_update.message.reply_to_message.caption = "Photo caption"
        mock_update.message.reply_to_message.message_id = 123
        
        command_handler.message_repository.save_message.return_value = 1
        
        # Execute
        await command_handler.handle_tag(mock_update, mock_context)
        
        # Verify repository call
        command_handler.message_repository.save_message.assert_called_once_with(
            chat_id=12345,
            message_id=123,
            content="Photo caption",
            saved_by=67890,
            tag="media"
        )
    
    @pytest.mark.asyncio
    async def test_tag_command_multimedia_no_text(self, command_handler, mock_update, mock_context):
        """Test tagging of multimedia message without text or caption"""
        # Setup
        mock_context.args = ["multimedia"]
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = None
        mock_update.message.reply_to_message.caption = None
        mock_update.message.reply_to_message.message_id = 123
        
        command_handler.message_repository.save_message.return_value = 1
        
        # Execute
        await command_handler.handle_tag(mock_update, mock_context)
        
        # Verify repository call
        command_handler.message_repository.save_message.assert_called_once_with(
            chat_id=12345,
            message_id=123,
            content="[Mensaje multimedia]",
            saved_by=67890,
            tag="multimedia"
        )
    
    @pytest.mark.asyncio
    async def test_tag_command_multi_word_tag(self, command_handler, mock_update, mock_context):
        """Test tagging with multi-word tag"""
        # Setup
        mock_context.args = ["very", "important", "message"]
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = "Test message"
        mock_update.message.reply_to_message.message_id = 123
        
        command_handler.message_repository.save_message.return_value = 1
        
        # Execute
        await command_handler.handle_tag(mock_update, mock_context)
        
        # Verify repository call with lowercase combined tag
        command_handler.message_repository.save_message.assert_called_once_with(
            chat_id=12345,
            message_id=123,
            content="Test message",
            saved_by=67890,
            tag="very important message"
        )
    
    @pytest.mark.asyncio
    async def test_tag_command_database_error(self, command_handler, mock_update, mock_context):
        """Test /tag command when database save fails"""
        # Setup
        mock_context.args = ["important"]
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = "Test message"
        mock_update.message.reply_to_message.message_id = 123
        
        command_handler.message_repository.save_message.return_value = None
        
        # Execute
        await command_handler.handle_tag(mock_update, mock_context)
        
        # Verify error response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "No se pudo etiquetar el mensaje" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_searchtag_command_no_arguments(self, command_handler, mock_update, mock_context):
        """Test /searchtag command without arguments"""
        # Setup
        mock_context.args = []
        
        # Execute
        await command_handler.handle_searchtag(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "No especificaste qué etiqueta buscar" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_searchtag_command_no_messages_found(self, command_handler, mock_update, mock_context):
        """Test /searchtag command when no messages are found"""
        # Setup
        mock_context.args = ["nonexistent"]
        command_handler.message_repository.get_messages_by_tag.return_value = []
        
        # Execute
        await command_handler.handle_searchtag(mock_update, mock_context)
        
        # Verify repository call
        command_handler.message_repository.get_messages_by_tag.assert_called_once_with(
            12345, "nonexistent"
        )
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "No se encontraron mensajes" in call_args[0][0]
        assert "nonexistent" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_searchtag_command_single_message(self, command_handler, mock_update, mock_context):
        """Test /searchtag command with single message result"""
        # Setup
        mock_context.args = ["important"]
        
        test_message = SavedMessage(
            id=1,
            chat_id=12345,
            message_id=123,
            content="This is an important message",
            tag="important",
            saved_by=67890,
            created_at=datetime(2024, 1, 15, 10, 30)
        )
        
        command_handler.message_repository.get_messages_by_tag.return_value = [test_message]
        
        # Execute
        await command_handler.handle_searchtag(mock_update, mock_context)
        
        # Verify repository call
        command_handler.message_repository.get_messages_by_tag.assert_called_once_with(
            12345, "important"
        )
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "MENSAJES ETIQUETADOS: IMPORTANT" in response_text
        assert "15/01/2024 10:30" in response_text
        assert "This is an important message" in response_text
        assert "Total: 1 mensajes" in response_text
    
    @pytest.mark.asyncio
    async def test_searchtag_command_multiple_messages(self, command_handler, mock_update, mock_context):
        """Test /searchtag command with multiple message results"""
        # Setup
        mock_context.args = ["work"]
        
        test_messages = [
            SavedMessage(
                id=1,
                chat_id=12345,
                message_id=123,
                content="First work message",
                tag="work",
                saved_by=67890,
                created_at=datetime(2024, 1, 15, 10, 30)
            ),
            SavedMessage(
                id=2,
                chat_id=12345,
                message_id=124,
                content="Second work message",
                tag="work",
                saved_by=67890,
                created_at=datetime(2024, 1, 16, 11, 45)
            )
        ]
        
        command_handler.message_repository.get_messages_by_tag.return_value = test_messages
        
        # Execute
        await command_handler.handle_searchtag(mock_update, mock_context)
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "MENSAJES ETIQUETADOS: WORK" in response_text
        assert "First work message" in response_text
        assert "Second work message" in response_text
        assert "Total: 2 mensajes" in response_text
    
    @pytest.mark.asyncio
    async def test_searchtag_command_long_message_truncation(self, command_handler, mock_update, mock_context):
        """Test /searchtag command truncates long messages"""
        # Setup
        mock_context.args = ["long"]
        
        long_content = "A" * 200  # 200 characters, should be truncated
        test_message = SavedMessage(
            id=1,
            chat_id=12345,
            message_id=123,
            content=long_content,
            tag="long",
            saved_by=67890,
            created_at=datetime(2024, 1, 15, 10, 30)
        )
        
        command_handler.message_repository.get_messages_by_tag.return_value = [test_message]
        
        # Execute
        await command_handler.handle_searchtag(mock_update, mock_context)
        
        # Verify response contains truncated content
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "A" * 147 + "..." in response_text  # Should be truncated to 147 chars + "..."
    
    @pytest.mark.asyncio
    async def test_searchtag_command_multi_word_tag(self, command_handler, mock_update, mock_context):
        """Test /searchtag command with multi-word tag"""
        # Setup
        mock_context.args = ["very", "important"]
        
        test_message = SavedMessage(
            id=1,
            chat_id=12345,
            message_id=123,
            content="Test message",
            tag="very important",
            saved_by=67890,
            created_at=datetime(2024, 1, 15, 10, 30)
        )
        
        command_handler.message_repository.get_messages_by_tag.return_value = [test_message]
        
        # Execute
        await command_handler.handle_searchtag(mock_update, mock_context)
        
        # Verify repository call with combined tag
        command_handler.message_repository.get_messages_by_tag.assert_called_once_with(
            12345, "very important"
        )
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "MENSAJES ETIQUETADOS: VERY IMPORTANT" in response_text
    
    @pytest.mark.asyncio
    async def test_searchtag_command_database_error(self, command_handler, mock_update, mock_context):
        """Test /searchtag command when database query fails"""
        # Setup
        mock_context.args = ["error"]
        command_handler.message_repository.get_messages_by_tag.side_effect = Exception("Database error")
        
        # Execute
        await command_handler.handle_searchtag(mock_update, mock_context)
        
        # Verify error response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        # Should contain error message from theme engine
        assert call_args[1]["parse_mode"] == "Markdown"
    
    @pytest.mark.asyncio
    async def test_tag_command_humorous_tone(self, mock_update, mock_context):
        """Test /tag command with humorous tone"""
        # Setup with humorous theme
        theme_engine = ThemeEngine(ToneStyle.HUMOROUS)
        with patch('handlers.commands.get_database_manager'):
            handler = CommandHandler(theme_engine)
            handler.message_repository = Mock()
        
        mock_context.args = ["funny"]
        mock_update.message.reply_to_message = Mock(spec=Message)
        mock_update.message.reply_to_message.text = "Funny message"
        mock_update.message.reply_to_message.message_id = 123
        
        handler.message_repository.save_message.return_value = 1
        
        # Execute
        await handler.handle_tag(mock_update, mock_context)
        
        # Verify response contains humorous language
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "negocios etiquetados" in response_text
    
    @pytest.mark.asyncio
    async def test_searchtag_command_humorous_tone(self, mock_update, mock_context):
        """Test /searchtag command with humorous tone"""
        # Setup with humorous theme
        theme_engine = ThemeEngine(ToneStyle.HUMOROUS)
        with patch('handlers.commands.get_database_manager'):
            handler = CommandHandler(theme_engine)
            handler.message_repository = Mock()
        
        mock_context.args = ["funny"]
        handler.message_repository.get_messages_by_tag.return_value = []
        
        # Execute
        await handler.handle_searchtag(mock_update, mock_context)
        
        # Verify response contains humorous language
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        response_text = call_args[0][0]
        assert "negocios etiquetados" in response_text