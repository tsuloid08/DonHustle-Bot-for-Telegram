"""
Tests for custom commands functionality in @donhustle_bot
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from telegram import Update, Message, User, Chat, ChatMember
from telegram.ext import ContextTypes

from handlers.commands import CommandHandler
from database.manager import DatabaseManager
from database.repositories import CustomCommandRepository
from database.models import CustomCommand
from utils.theme import ThemeEngine, ToneStyle


@pytest.fixture
def db_manager():
    """Create a test database manager."""
    return DatabaseManager(":memory:")


@pytest.fixture
def theme_engine():
    """Create a theme engine for testing."""
    return ThemeEngine(ToneStyle.SERIOUS)


@pytest.fixture
def command_handler(db_manager, theme_engine):
    """Create a command handler for testing."""
    return CommandHandler(theme_engine)


@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
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
def mock_context():
    """Create a mock Telegram context."""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    context.bot = Mock()
    context.bot.get_chat_member = AsyncMock()
    context.application = Mock()
    context.application.add_handler = Mock()
    return context


@pytest.fixture
def mock_admin_chat_member():
    """Create a mock admin chat member."""
    member = Mock(spec=ChatMember)
    member.status = "administrator"
    return member


@pytest.fixture
def mock_regular_chat_member():
    """Create a mock regular chat member."""
    member = Mock(spec=ChatMember)
    member.status = "member"
    return member


class TestCustomCommandCreation:
    """Test custom command creation functionality."""
    
    @pytest.mark.asyncio
    async def test_addcommand_success(self, command_handler, mock_update, mock_context, mock_admin_chat_member):
        """Test successful custom command creation."""
        mock_context.args = ["testcmd", "This", "is", "a", "test", "response"]
        mock_context.bot.get_chat_member.return_value = mock_admin_chat_member
        
        with patch.object(command_handler.custom_command_repository, 'get_custom_command', return_value=None), \
             patch.object(command_handler.custom_command_repository, 'add_custom_command', return_value=1), \
             patch.object(command_handler, '_register_custom_command', new_callable=AsyncMock):
            
            await command_handler.handle_addcommand(mock_update, mock_context)
            
            # Verify success message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Nuevo comando creado" in call_args
            assert "/testcmd" in call_args
    
    @pytest.mark.asyncio
    async def test_addcommand_update_existing(self, command_handler, mock_update, mock_context, mock_admin_chat_member):
        """Test updating an existing custom command."""
        mock_context.args = ["existingcmd", "Updated", "response"]
        mock_context.bot.get_chat_member.return_value = mock_admin_chat_member
        
        existing_command = CustomCommand(
            id=1,
            chat_id=12345,
            command_name="existingcmd",
            response="Old response",
            created_by=67890
        )
        
        with patch.object(command_handler.custom_command_repository, 'get_custom_command', return_value=existing_command), \
             patch.object(command_handler.custom_command_repository, 'delete_custom_command', return_value=True), \
             patch.object(command_handler.custom_command_repository, 'add_custom_command', return_value=2), \
             patch.object(command_handler, '_register_custom_command', new_callable=AsyncMock):
            
            await command_handler.handle_addcommand(mock_update, mock_context)
            
            # Verify update message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Comando actualizado" in call_args
            assert "/existingcmd" in call_args
    
    @pytest.mark.asyncio
    async def test_addcommand_insufficient_args(self, command_handler, mock_update, mock_context, mock_admin_chat_member):
        """Test addcommand with insufficient arguments."""
        mock_context.args = ["onlyname"]
        mock_context.bot.get_chat_member.return_value = mock_admin_chat_member
        
        await command_handler.handle_addcommand(mock_update, mock_context)
        
        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Faltan parámetros" in call_args
    
    @pytest.mark.asyncio
    async def test_addcommand_invalid_name(self, command_handler, mock_update, mock_context, mock_admin_chat_member):
        """Test addcommand with invalid command name."""
        mock_context.args = ["123invalid", "response"]
        mock_context.bot.get_chat_member.return_value = mock_admin_chat_member
        
        await command_handler.handle_addcommand(mock_update, mock_context)
        
        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Nombre de comando inválido" in call_args
    
    @pytest.mark.asyncio
    async def test_addcommand_reserved_name(self, command_handler, mock_update, mock_context, mock_admin_chat_member):
        """Test addcommand with reserved command name."""
        mock_context.args = ["start", "response"]
        mock_context.bot.get_chat_member.return_value = mock_admin_chat_member
        
        await command_handler.handle_addcommand(mock_update, mock_context)
        
        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "está reservado" in call_args
    
    @pytest.mark.asyncio
    async def test_addcommand_non_admin(self, command_handler, mock_update, mock_context, mock_regular_chat_member):
        """Test addcommand by non-admin user."""
        mock_context.args = ["testcmd", "response"]
        mock_context.bot.get_chat_member.return_value = mock_regular_chat_member
        
        await command_handler.handle_addcommand(mock_update, mock_context)
        
        # Verify warning message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Solo los administradores" in call_args


class TestCustomCommandListing:
    """Test custom command listing functionality."""
    
    @pytest.mark.asyncio
    async def test_customcommands_with_commands(self, command_handler, mock_update, mock_context):
        """Test listing custom commands when commands exist."""
        commands = [
            CustomCommand(
                id=1,
                chat_id=12345,
                command_name="cmd1",
                response="Response 1",
                created_by=67890
            ),
            CustomCommand(
                id=2,
                chat_id=12345,
                command_name="cmd2",
                response="Response 2",
                created_by=67890
            )
        ]
        
        with patch.object(command_handler.custom_command_repository, 'get_all_custom_commands', return_value=commands):
            await command_handler.handle_customcommands(mock_update, mock_context)
            
            # Verify commands list was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "/cmd1" in call_args
            assert "/cmd2" in call_args
            assert "Total: 2 comandos" in call_args
    
    @pytest.mark.asyncio
    async def test_customcommands_empty(self, command_handler, mock_update, mock_context):
        """Test listing custom commands when no commands exist."""
        with patch.object(command_handler.custom_command_repository, 'get_all_custom_commands', return_value=[]):
            await command_handler.handle_customcommands(mock_update, mock_context)
            
            # Verify empty message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "No hay comandos personalizados" in call_args


class TestCustomCommandDeletion:
    """Test custom command deletion functionality."""
    
    @pytest.mark.asyncio
    async def test_deletecommand_success(self, command_handler, mock_update, mock_context, mock_admin_chat_member):
        """Test successful custom command deletion."""
        mock_context.args = ["testcmd"]
        mock_context.bot.get_chat_member.return_value = mock_admin_chat_member
        
        existing_command = CustomCommand(
            id=1,
            chat_id=12345,
            command_name="testcmd",
            response="Test response",
            created_by=67890
        )
        
        with patch.object(command_handler.custom_command_repository, 'get_custom_command', return_value=existing_command), \
             patch.object(command_handler.custom_command_repository, 'delete_custom_command', return_value=True), \
             patch.object(command_handler, '_unregister_custom_command', new_callable=AsyncMock):
            
            await command_handler.handle_deletecommand(mock_update, mock_context)
            
            # Verify success message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Comando eliminado" in call_args
            assert "/testcmd" in call_args
    
    @pytest.mark.asyncio
    async def test_deletecommand_not_found(self, command_handler, mock_update, mock_context, mock_admin_chat_member):
        """Test deleting non-existent custom command."""
        mock_context.args = ["nonexistent"]
        mock_context.bot.get_chat_member.return_value = mock_admin_chat_member
        
        with patch.object(command_handler.custom_command_repository, 'get_custom_command', return_value=None):
            await command_handler.handle_deletecommand(mock_update, mock_context)
            
            # Verify error message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "no existe" in call_args
    
    @pytest.mark.asyncio
    async def test_deletecommand_no_args(self, command_handler, mock_update, mock_context, mock_admin_chat_member):
        """Test deletecommand without arguments."""
        mock_context.args = []
        mock_context.bot.get_chat_member.return_value = mock_admin_chat_member
        
        await command_handler.handle_deletecommand(mock_update, mock_context)
        
        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "No especificaste" in call_args


class TestCustomCommandExecution:
    """Test custom command execution functionality."""
    
    @pytest.mark.asyncio
    async def test_custom_command_execution(self, command_handler, mock_update, mock_context):
        """Test executing a custom command."""
        custom_command = CustomCommand(
            id=1,
            chat_id=12345,
            command_name="testcmd",
            response="This is a test response",
            created_by=67890
        )
        
        with patch.object(command_handler.custom_command_repository, 'get_custom_command', return_value=custom_command):
            await command_handler.handle_custom_command_execution(mock_update, mock_context, "testcmd")
            
            # Verify response was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "This is a test response" in call_args
    
    @pytest.mark.asyncio
    async def test_custom_command_execution_not_found(self, command_handler, mock_update, mock_context):
        """Test executing non-existent custom command."""
        with patch.object(command_handler.custom_command_repository, 'get_custom_command', return_value=None):
            await command_handler.handle_custom_command_execution(mock_update, mock_context, "nonexistent")
            
            # Should not send any message for non-existent commands
            mock_update.message.reply_text.assert_not_called()


class TestCustomCommandRegistration:
    """Test custom command registration functionality."""
    
    @pytest.mark.asyncio
    async def test_register_custom_command(self, command_handler, mock_context):
        """Test registering a custom command with the application."""
        mock_application = Mock()
        mock_application.add_handler = Mock()
        
        await command_handler._register_custom_command(mock_application, 12345, "testcmd")
        
        # Verify handler was added
        mock_application.add_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_and_register_custom_commands(self, command_handler):
        """Test loading and registering all custom commands from database."""
        mock_application = Mock()
        mock_application.add_handler = Mock()
        
        # Mock database cursor
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'chat_id': 12345, 'command_name': 'cmd1'},
            {'chat_id': 12345, 'command_name': 'cmd2'},
            {'chat_id': 67890, 'command_name': 'cmd3'}
        ]
        
        with patch.object(command_handler.db_manager, 'get_cursor') as mock_get_cursor, \
             patch.object(command_handler, '_register_custom_command', new_callable=AsyncMock) as mock_register:
            
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor
            
            await command_handler.load_and_register_custom_commands(mock_application)
            
            # Verify all commands were registered
            assert mock_register.call_count == 3
            mock_register.assert_any_call(mock_application, 12345, 'cmd1')
            mock_register.assert_any_call(mock_application, 12345, 'cmd2')
            mock_register.assert_any_call(mock_application, 67890, 'cmd3')


class TestCustomCommandRepository:
    """Test custom command repository functionality."""
    
    def test_add_custom_command(self, db_manager):
        """Test adding a custom command to the database."""
        repo = CustomCommandRepository(db_manager)
        
        command_id = repo.add_custom_command(12345, "testcmd", "Test response", 67890)
        
        assert command_id is not None
        assert command_id > 0
    
    def test_get_custom_command(self, db_manager):
        """Test retrieving a custom command from the database."""
        repo = CustomCommandRepository(db_manager)
        
        # Add a command first
        command_id = repo.add_custom_command(12345, "testcmd", "Test response", 67890)
        
        # Retrieve it
        command = repo.get_custom_command(12345, "testcmd")
        
        assert command is not None
        assert command.command_name == "testcmd"
        assert command.response == "Test response"
        assert command.chat_id == 12345
        assert command.created_by == 67890
    
    def test_get_all_custom_commands(self, db_manager):
        """Test retrieving all custom commands for a chat."""
        repo = CustomCommandRepository(db_manager)
        
        # Add multiple commands
        repo.add_custom_command(12345, "cmd1", "Response 1", 67890)
        repo.add_custom_command(12345, "cmd2", "Response 2", 67890)
        repo.add_custom_command(54321, "cmd3", "Response 3", 67890)  # Different chat
        
        # Get commands for chat 12345
        commands = repo.get_all_custom_commands(12345)
        
        assert len(commands) == 2
        command_names = [cmd.command_name for cmd in commands]
        assert "cmd1" in command_names
        assert "cmd2" in command_names
        assert "cmd3" not in command_names
    
    def test_delete_custom_command(self, db_manager):
        """Test deleting a custom command from the database."""
        repo = CustomCommandRepository(db_manager)
        
        # Add a command first
        repo.add_custom_command(12345, "testcmd", "Test response", 67890)
        
        # Verify it exists
        command = repo.get_custom_command(12345, "testcmd")
        assert command is not None
        
        # Delete it
        result = repo.delete_custom_command(12345, "testcmd")
        assert result is True
        
        # Verify it's gone
        command = repo.get_custom_command(12345, "testcmd")
        assert command is None
    
    def test_unique_constraint(self, db_manager):
        """Test that command names are unique per chat."""
        repo = CustomCommandRepository(db_manager)
        
        # Add a command
        repo.add_custom_command(12345, "testcmd", "Response 1", 67890)
        
        # Try to add another command with the same name in the same chat
        with pytest.raises(Exception):  # Should raise a database constraint error
            repo.add_custom_command(12345, "testcmd", "Response 2", 67890)
        
        # But should work in a different chat
        command_id = repo.add_custom_command(54321, "testcmd", "Response 2", 67890)
        assert command_id is not None


if __name__ == "__main__":
    pytest.main([__file__])