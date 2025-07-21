"""
Handlers package for Telegram bot commands and message processing
"""

from handlers.commands import register_command_handlers
from handlers.error_handler import register_error_handler
from handlers.welcome_handler import register_welcome_handlers

__all__ = ['register_command_handlers', 'register_error_handler', 'register_welcome_handlers']