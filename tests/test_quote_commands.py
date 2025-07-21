"""
Unit tests for quote management commands in @donhustle_bot
Tests all quote-related command handlers with mock data
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from telegram import Update, Message, Chat, User
from telegram.ext import ContextTypes

from handlers.commands import CommandHandler
from utils.theme import ThemeEngine, ToneStyle
from database.models import Quote
from database.repositories import QuoteRepository


class TestQuoteCommands:
    """Test class for quote management commands"""
    
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
    def mock_quote_repository(self):
        """Create a mock quote repository"""
        return Mock(spec=QuoteRepository)
    
    @pytest.fixture
    def command_handler(self, theme_engine, mock_db_manager, mock_quote_repository):
        """Create a command handler with mocked dependencies"""
        with patch('handlers.commands.get_database_manager', return_value=mock_db_manager):
            with patch('handlers.commands.QuoteRepository', return_value=mock_quote_repository):
                handler = CommandHandler(theme_engine)
                handler.quote_repository = mock_quote_repository
                return handler
    
    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update"""
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 12345
        update.effective_user.first_name = "TestUser"
        
        update.effective_chat = Mock(spec=Chat)
        update.effective_chat.id = 67890
        update.effective_chat.type = "group"
        
        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.effective_message = update.message
        
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Telegram context"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        return context
    
    @pytest.fixture
    def sample_quotes(self):
        """Create sample quotes for testing"""
        return [
            Quote(id=1, quote="El éxito requiere trabajo duro", created_at=datetime.now()),
            Quote(id=2, quote="La persistencia es la clave del éxito", created_at=datetime.now()),
            Quote(id=3, quote="No hay atajos hacia el éxito", created_at=datetime.now())
        ]

    @pytest.mark.asyncio
    async def test_handle_listquotes_with_quotes(self, command_handler, mock_update, mock_context, sample_quotes):
        """Test /listquotes command when quotes exist"""
        # Setup
        command_handler.quote_repository.get_all_quotes.return_value = sample_quotes
        
        # Execute
        await command_handler.handle_listquotes(mock_update, mock_context)
        
        # Verify
        command_handler.quote_repository.get_all_quotes.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
        
        # Check that the message contains the quotes
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "LIBRO DE FRASES DE LA FAMILIA" in message_text
        assert "El éxito requiere trabajo duro" in message_text
        assert "La persistencia es la clave del éxito" in message_text
        assert "Total: 3 frases" in message_text

    @pytest.mark.asyncio
    async def test_handle_listquotes_no_quotes(self, command_handler, mock_update, mock_context):
        """Test /listquotes command when no quotes exist"""
        # Setup
        command_handler.quote_repository.get_all_quotes.return_value = []
        
        # Execute
        await command_handler.handle_listquotes(mock_update, mock_context)
        
        # Verify
        command_handler.quote_repository.get_all_quotes.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
        
        # Check warning message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "No hay frases en el libro de la familia" in message_text
        assert "/addhustle" in message_text

    @pytest.mark.asyncio
    async def test_handle_listquotes_many_quotes(self, command_handler, mock_update, mock_context):
        """Test /listquotes command with many quotes (chunking)"""
        # Setup - create 25 quotes to test chunking
        many_quotes = []
        for i in range(25):
            many_quotes.append(Quote(id=i+1, quote=f"Quote number {i+1}", created_at=datetime.now()))
        
        command_handler.quote_repository.get_all_quotes.return_value = many_quotes
        
        # Execute
        await command_handler.handle_listquotes(mock_update, mock_context)
        
        # Verify multiple messages were sent (chunking)
        assert mock_update.message.reply_text.call_count == 2  # Should be split into 2 messages

    @pytest.mark.asyncio
    async def test_handle_deletequote_success(self, command_handler, mock_update, mock_context, sample_quotes):
        """Test /deletequote command with valid quote index"""
        # Setup
        mock_context.args = ["2"]  # Delete second quote
        command_handler.quote_repository.get_all_quotes.return_value = sample_quotes
        command_handler.quote_repository.delete_quote.return_value = True
        
        # Execute
        await command_handler.handle_deletequote(mock_update, mock_context)
        
        # Verify
        command_handler.quote_repository.get_all_quotes.assert_called_once()
        command_handler.quote_repository.delete_quote.assert_called_once_with(2)  # ID of second quote
        mock_update.message.reply_text.assert_called_once()
        
        # Check success message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Frase eliminada" in message_text
        assert "La persistencia es la clave del éxito" in message_text

    @pytest.mark.asyncio
    async def test_handle_deletequote_no_args(self, command_handler, mock_update, mock_context):
        """Test /deletequote command without arguments"""
        # Setup - no arguments provided
        mock_context.args = []
        
        # Execute
        await command_handler.handle_deletequote(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "No especificaste qué frase eliminar" in message_text
        assert "/deletequote [número]" in message_text

    @pytest.mark.asyncio
    async def test_handle_deletequote_invalid_index(self, command_handler, mock_update, mock_context, sample_quotes):
        """Test /deletequote command with invalid quote index"""
        # Setup
        mock_context.args = ["10"]  # Index out of range
        command_handler.quote_repository.get_all_quotes.return_value = sample_quotes
        
        # Execute
        await command_handler.handle_deletequote(mock_update, mock_context)
        
        # Verify
        command_handler.quote_repository.get_all_quotes.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Número de frase inválido: 10" in message_text
        assert "entre 1 y 3" in message_text

    @pytest.mark.asyncio
    async def test_handle_deletequote_non_numeric(self, command_handler, mock_update, mock_context):
        """Test /deletequote command with non-numeric argument"""
        # Setup
        mock_context.args = ["abc"]
        
        # Execute
        await command_handler.handle_deletequote(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "número válido" in message_text

    @pytest.mark.asyncio
    async def test_handle_clearquotes_confirmation_request(self, command_handler, mock_update, mock_context, sample_quotes):
        """Test /clearquotes command asking for confirmation"""
        # Setup
        mock_context.args = []  # No confirmation provided
        command_handler.quote_repository.get_all_quotes.return_value = sample_quotes
        
        # Execute
        await command_handler.handle_clearquotes(mock_update, mock_context)
        
        # Verify
        command_handler.quote_repository.get_all_quotes.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
        
        # Check confirmation request
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "todas las 3 frases" in message_text
        assert "/clearquotes confirmar" in message_text

    @pytest.mark.asyncio
    async def test_handle_clearquotes_confirmed(self, command_handler, mock_update, mock_context, sample_quotes):
        """Test /clearquotes command with confirmation"""
        # Setup
        mock_context.args = ["confirmar"]
        command_handler.quote_repository.get_all_quotes.return_value = sample_quotes
        command_handler.quote_repository.clear_all_quotes.return_value = 3
        
        # Execute
        await command_handler.handle_clearquotes(mock_update, mock_context)
        
        # Verify
        command_handler.quote_repository.get_all_quotes.assert_called_once()
        command_handler.quote_repository.clear_all_quotes.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
        
        # Check success message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "3 frases" in message_text
        assert "eliminadas del archivo" in message_text

    @pytest.mark.asyncio
    async def test_handle_clearquotes_no_quotes(self, command_handler, mock_update, mock_context):
        """Test /clearquotes command when no quotes exist"""
        # Setup
        command_handler.quote_repository.get_all_quotes.return_value = []
        
        # Execute
        await command_handler.handle_clearquotes(mock_update, mock_context)
        
        # Verify
        command_handler.quote_repository.get_all_quotes.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
        
        # Check warning message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "No hay frases para limpiar" in message_text

    @pytest.mark.asyncio
    async def test_handle_addhustle_success(self, command_handler, mock_update, mock_context):
        """Test /addhustle command with valid quote"""
        # Setup
        mock_context.args = ["El", "trabajo", "duro", "siempre", "da", "frutos"]
        command_handler.quote_repository.add_quote.return_value = 123  # Mock quote ID
        
        # Execute
        await command_handler.handle_addhustle(mock_update, mock_context)
        
        # Verify
        expected_quote = "El trabajo duro siempre da frutos"
        command_handler.quote_repository.add_quote.assert_called_once_with(expected_quote)
        mock_update.message.reply_text.assert_called_once()
        
        # Check success message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Nueva frase agregada" in message_text
        assert expected_quote in message_text

    @pytest.mark.asyncio
    async def test_handle_addhustle_no_args(self, command_handler, mock_update, mock_context):
        """Test /addhustle command without arguments"""
        # Setup
        mock_context.args = []
        
        # Execute
        await command_handler.handle_addhustle(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "No especificaste la frase" in message_text
        assert "/addhustle [frase]" in message_text

    @pytest.mark.asyncio
    async def test_handle_addhustle_too_short(self, command_handler, mock_update, mock_context):
        """Test /addhustle command with too short quote"""
        # Setup
        mock_context.args = ["Corto"]  # Too short
        
        # Execute
        await command_handler.handle_addhustle(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "demasiado corta" in message_text

    @pytest.mark.asyncio
    async def test_handle_addhustle_too_long(self, command_handler, mock_update, mock_context):
        """Test /addhustle command with too long quote"""
        # Setup - create a quote that's definitely over 500 characters
        # Each "palabra" is 7 characters + 1 space = 8 characters
        # 70 words * 8 = 560 characters, which is over 500
        long_quote = ["palabra"] * 70
        mock_context.args = long_quote
        
        # Execute
        await command_handler.handle_addhustle(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "demasiado larga" in message_text
        assert "500 caracteres" in message_text

    @pytest.mark.asyncio
    async def test_handle_addhustle_database_error(self, command_handler, mock_update, mock_context):
        """Test /addhustle command when database operation fails"""
        # Setup
        mock_context.args = ["Una", "frase", "válida", "para", "agregar"]
        command_handler.quote_repository.add_quote.return_value = None  # Simulate failure
        
        # Execute
        await command_handler.handle_addhustle(mock_update, mock_context)
        
        # Verify
        command_handler.quote_repository.add_quote.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "No se pudo agregar la frase" in message_text

    @pytest.mark.asyncio
    async def test_quote_commands_exception_handling(self, command_handler, mock_update, mock_context):
        """Test that quote commands handle exceptions gracefully"""
        # Setup - make repository throw exception
        command_handler.quote_repository.get_all_quotes.side_effect = Exception("Database error")
        
        # Execute
        await command_handler.handle_listquotes(mock_update, mock_context)
        
        # Verify error handling
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        # Should contain an error message from theme engine
        assert len(message_text) > 0  # At least some error message was sent

    def test_quote_commands_integration_with_theme_engine(self, command_handler, sample_quotes):
        """Test that quote commands properly integrate with theme engine"""
        # Test that theme engine is used for message generation
        assert command_handler.theme_engine is not None
        
        # Test different tone styles
        command_handler.theme_engine.set_tone(ToneStyle.HUMOROUS)
        assert command_handler.theme_engine.get_tone() == ToneStyle.HUMOROUS
        
        command_handler.theme_engine.set_tone(ToneStyle.SERIOUS)
        assert command_handler.theme_engine.get_tone() == ToneStyle.SERIOUS


if __name__ == "__main__":
    pytest.main([__file__])