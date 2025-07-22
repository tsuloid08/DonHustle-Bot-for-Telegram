"""
Integration tests for the /uploadquotes command workflow.
Tests the complete file upload and processing pipeline.
"""
import os
import json
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, Document, User, Chat
from telegram.ext import ContextTypes

from handlers.commands import CommandHandler
from utils.theme import ThemeEngine, ToneStyle
from database.manager import get_database_manager


class TestUploadQuotesIntegration:
    """Integration test suite for /uploadquotes command."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Initialize theme engine and command handler
        self.theme_engine = ThemeEngine(ToneStyle.SERIOUS)
        self.command_handler = CommandHandler(self.theme_engine)
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Set up test database
        self.db_manager = get_database_manager(":memory:")
        self.command_handler.db_manager = self.db_manager
        
        # Mock objects
        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = 12345
        self.mock_user.first_name = "TestUser"
        
        self.mock_chat = MagicMock(spec=Chat)
        self.mock_chat.id = 67890
        self.mock_chat.type = "group"
        
        self.mock_context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        self.mock_context.bot = AsyncMock()
    
    def teardown_method(self):
        """Clean up after each test."""
        self.temp_dir.cleanup()
    
    def create_temp_file(self, content, filename):
        """Helper to create temporary test files."""
        file_path = os.path.join(self.temp_dir.name, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def create_mock_update_with_document(self, filename, file_content, file_size=1024):
        """Create a mock update with document attachment."""
        # Create temporary file
        file_path = self.create_temp_file(file_content, filename)
        
        # Mock document
        mock_document = MagicMock(spec=Document)
        mock_document.file_name = filename
        mock_document.file_size = file_size
        mock_document.file_id = f"test_file_id_{filename}"
        
        # Mock message
        mock_message = MagicMock(spec=Message)
        mock_message.document = mock_document
        mock_message.reply_text = AsyncMock()
        
        # Mock update
        mock_update = MagicMock(spec=Update)
        mock_update.effective_user = self.mock_user
        mock_update.effective_chat = self.mock_chat
        mock_update.message = mock_message
        mock_update.effective_message = mock_message
        
        return mock_update, file_path
    
    @pytest.mark.asyncio
    async def test_upload_txt_file_success(self):
        """Test successful upload of a .txt file with quotes."""
        # Prepare test data
        txt_content = "Trabajo duro es la clave del éxito\nLa familia siempre es primero\nRespeto se gana con acciones"
        mock_update, file_path = self.create_mock_update_with_document("quotes.txt", txt_content)
        
        # Mock admin check
        mock_chat_member = MagicMock()
        mock_chat_member.status = "administrator"
        self.mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Mock file download
        mock_file = MagicMock()
        mock_file.download_to_drive = AsyncMock()
        self.mock_context.bot.get_file.return_value = mock_file
        
        # Mock processing message
        mock_processing_message = MagicMock()
        mock_processing_message.edit_text = AsyncMock()
        mock_update.message.reply_text.return_value = mock_processing_message
        
        # Execute the command
        await self.command_handler.handle_uploadquotes(mock_update, self.mock_context)
        
        # Verify admin check was performed
        self.mock_context.bot.get_chat_member.assert_called_once_with(67890, 12345)
        
        # Verify file download was attempted
        self.mock_context.bot.get_file.assert_called_once()
        
        # Verify processing message was sent
        mock_update.message.reply_text.assert_called_once()
        
        # Verify success message was edited
        mock_processing_message.edit_text.assert_called()
        
        # Check that success message contains the expected text
        edit_calls = mock_processing_message.edit_text.call_args_list
        success_call = edit_calls[-1]  # Last call should be success message
        success_text = success_call[0][0]  # First argument
        
        assert "Capo, las frases han sido añadidas al libro de la familia" in success_text
        assert "3" in success_text  # Should mention 3 quotes added
    
    @pytest.mark.asyncio
    async def test_upload_csv_file_success(self):
        """Test successful upload of a .csv file with quotes."""
        # Prepare test data
        csv_content = "id,quote,author\n1,El éxito requiere sacrificio,Don Corleone\n2,La familia es todo,Vito Corleone"
        mock_update, file_path = self.create_mock_update_with_document("quotes.csv", csv_content)
        
        # Mock admin check
        mock_chat_member = MagicMock()
        mock_chat_member.status = "creator"
        self.mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Mock file download
        mock_file = MagicMock()
        mock_file.download_to_drive = AsyncMock()
        self.mock_context.bot.get_file.return_value = mock_file
        
        # Mock processing message
        mock_processing_message = MagicMock()
        mock_processing_message.edit_text = AsyncMock()
        mock_update.message.reply_text.return_value = mock_processing_message
        
        # Execute the command
        await self.command_handler.handle_uploadquotes(mock_update, self.mock_context)
        
        # Verify success message contains expected content
        edit_calls = mock_processing_message.edit_text.call_args_list
        success_call = edit_calls[-1]
        success_text = success_call[0][0]
        
        assert "Capo, las frases han sido añadidas al libro de la familia" in success_text
        assert "2" in success_text  # Should mention 2 quotes added
    
    @pytest.mark.asyncio
    async def test_upload_json_file_success(self):
        """Test successful upload of a .json file with quotes."""
        # Prepare test data
        quotes_array = [
            "La paciencia es una virtud de los fuertes",
            "El poder sin respeto no es nada",
            "Los negocios son personales cuando afectan a la familia"
        ]
        json_content = json.dumps(quotes_array)
        mock_update, file_path = self.create_mock_update_with_document("quotes.json", json_content)
        
        # Mock admin check
        mock_chat_member = MagicMock()
        mock_chat_member.status = "administrator"
        self.mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Mock file download
        mock_file = MagicMock()
        mock_file.download_to_drive = AsyncMock()
        self.mock_context.bot.get_file.return_value = mock_file
        
        # Mock processing message
        mock_processing_message = MagicMock()
        mock_processing_message.edit_text = AsyncMock()
        mock_update.message.reply_text.return_value = mock_processing_message
        
        # Execute the command
        await self.command_handler.handle_uploadquotes(mock_update, self.mock_context)
        
        # Verify success message
        edit_calls = mock_processing_message.edit_text.call_args_list
        success_call = edit_calls[-1]
        success_text = success_call[0][0]
        
        assert "Capo, las frases han sido añadidas al libro de la familia" in success_text
        assert "3" in success_text  # Should mention 3 quotes added
    
    @pytest.mark.asyncio
    async def test_upload_no_document_error(self):
        """Test error when no document is attached."""
        # Create mock update without document
        mock_message = MagicMock(spec=Message)
        mock_message.document = None
        mock_message.reply_text = AsyncMock()
        
        mock_update = MagicMock(spec=Update)
        mock_update.effective_user = self.mock_user
        mock_update.effective_chat = self.mock_chat
        mock_update.message = mock_message
        
        # Mock admin check
        mock_chat_member = MagicMock()
        mock_chat_member.status = "administrator"
        self.mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Execute the command
        await self.command_handler.handle_uploadquotes(mock_update, self.mock_context)
        
        # Verify error message was sent
        mock_message.reply_text.assert_called_once()
        error_call = mock_message.reply_text.call_args
        error_text = error_call[0][0]
        
        assert "No se encontró ningún archivo adjunto" in error_text
        assert "Adjunta un archivo .txt, .csv o .json" in error_text
    
    @pytest.mark.asyncio
    async def test_upload_unsupported_format_error(self):
        """Test error when uploading unsupported file format."""
        # Create mock update with unsupported file
        mock_update, _ = self.create_mock_update_with_document("document.pdf", "some content")
        
        # Mock admin check
        mock_chat_member = MagicMock()
        mock_chat_member.status = "administrator"
        self.mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Execute the command
        await self.command_handler.handle_uploadquotes(mock_update, self.mock_context)
        
        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once()
        error_call = mock_update.message.reply_text.call_args
        error_text = error_call[0][0]
        
        assert "Capo, ese archivo no es de la familia" in error_text
        assert "Solo acepto .txt, .csv o .json" in error_text
    
    @pytest.mark.asyncio
    async def test_upload_file_too_large_error(self):
        """Test error when file is too large."""
        # Create mock update with large file
        large_file_size = 15 * 1024 * 1024  # 15MB
        mock_update, _ = self.create_mock_update_with_document("quotes.txt", "content", large_file_size)
        
        # Mock admin check
        mock_chat_member = MagicMock()
        mock_chat_member.status = "administrator"
        self.mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Execute the command
        await self.command_handler.handle_uploadquotes(mock_update, self.mock_context)
        
        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once()
        error_call = mock_update.message.reply_text.call_args
        error_text = error_call[0][0]
        
        assert "El archivo es demasiado grande" in error_text
        assert "menor a 10MB" in error_text
    
    @pytest.mark.asyncio
    async def test_upload_non_admin_permission_error(self):
        """Test error when non-admin tries to upload."""
        # Create mock update
        mock_update, _ = self.create_mock_update_with_document("quotes.txt", "content")
        
        # Mock non-admin user
        mock_chat_member = MagicMock()
        mock_chat_member.status = "member"
        self.mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Execute the command
        await self.command_handler.handle_uploadquotes(mock_update, self.mock_context)
        
        # Verify permission error was sent
        mock_update.message.reply_text.assert_called_once()
        error_call = mock_update.message.reply_text.call_args
        error_text = error_call[0][0]
        
        assert "Solo los administradores pueden subir archivos de frases" in error_text
    
    @pytest.mark.asyncio
    async def test_upload_empty_file_warning(self):
        """Test warning when file contains no valid quotes."""
        # Create file with only empty lines and short quotes
        empty_content = "\n\n   \nhi\n\n"
        mock_update, file_path = self.create_mock_update_with_document("empty.txt", empty_content)
        
        # Mock admin check
        mock_chat_member = MagicMock()
        mock_chat_member.status = "administrator"
        self.mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Mock file download
        mock_file = MagicMock()
        mock_file.download_to_drive = AsyncMock()
        self.mock_context.bot.get_file.return_value = mock_file
        
        # Mock processing message
        mock_processing_message = MagicMock()
        mock_processing_message.edit_text = AsyncMock()
        mock_update.message.reply_text.return_value = mock_processing_message
        
        # Execute the command
        await self.command_handler.handle_uploadquotes(mock_update, self.mock_context)
        
        # Verify warning message was edited
        edit_calls = mock_processing_message.edit_text.call_args_list
        warning_call = edit_calls[-1]
        warning_text = warning_call[0][0]
        
        assert "Archivo vacío" in warning_text
        assert "no contiene frases válidas" in warning_text
    
    @pytest.mark.asyncio
    async def test_upload_private_chat_success(self):
        """Test successful upload in private chat (no admin check needed)."""
        # Set up private chat
        self.mock_chat.type = "private"
        
        # Prepare test data
        txt_content = "Frase de prueba para chat privado"
        mock_update, file_path = self.create_mock_update_with_document("quotes.txt", txt_content)
        
        # Mock file download
        mock_file = MagicMock()
        mock_file.download_to_drive = AsyncMock()
        self.mock_context.bot.get_file.return_value = mock_file
        
        # Mock processing message
        mock_processing_message = MagicMock()
        mock_processing_message.edit_text = AsyncMock()
        mock_update.message.reply_text.return_value = mock_processing_message
        
        # Execute the command
        await self.command_handler.handle_uploadquotes(mock_update, self.mock_context)
        
        # Verify no admin check was performed for private chat
        self.mock_context.bot.get_chat_member.assert_not_called()
        
        # Verify success message
        edit_calls = mock_processing_message.edit_text.call_args_list
        success_call = edit_calls[-1]
        success_text = success_call[0][0]
        
        assert "Capo, las frases han sido añadidas al libro de la familia" in success_text
    
    @pytest.mark.asyncio
    @patch('os.remove')
    async def test_upload_file_cleanup(self, mock_remove):
        """Test that temporary files are cleaned up after processing."""
        # Prepare test data
        txt_content = "Test quote for cleanup"
        mock_update, file_path = self.create_mock_update_with_document("quotes.txt", txt_content)
        
        # Mock admin check
        mock_chat_member = MagicMock()
        mock_chat_member.status = "administrator"
        self.mock_context.bot.get_chat_member.return_value = mock_chat_member
        
        # Mock file download
        mock_file = MagicMock()
        mock_file.download_to_drive = AsyncMock()
        self.mock_context.bot.get_file.return_value = mock_file
        
        # Mock processing message
        mock_processing_message = MagicMock()
        mock_processing_message.edit_text = AsyncMock()
        mock_update.message.reply_text.return_value = mock_processing_message
        
        # Execute the command
        await self.command_handler.handle_uploadquotes(mock_update, self.mock_context)
        
        # Verify temporary file cleanup was attempted
        mock_remove.assert_called_once()
        cleanup_call = mock_remove.call_args[0][0]
        assert cleanup_call.startswith("temp_")
        assert cleanup_call.endswith(".txt")