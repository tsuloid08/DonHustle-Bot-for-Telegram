"""
Error handler for @donhustle_bot
Implements mafia-themed error handling and logging
"""

import html
import json
import logging
import traceback
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.theme import ThemeEngine, MessageType

logger = logging.getLogger(__name__)
theme_engine = ThemeEngine()

async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors with mafia-themed messages and proper logging
    
    Args:
        update: Update that caused the error (may be None)
        context: Context with error information
    """
    # Log the error
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Extract traceback info
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    
    # Format error message for logging
    update_str = update.to_dict() if update else "No update"
    error_message = (
        f"Exception while handling an update\n"
        f"update = {json.dumps(update_str, indent=2, ensure_ascii=False)}\n\n"
        f"context.chat_data = {str(context.chat_data)}\n\n"
        f"context.user_data = {str(context.user_data)}\n\n"
        f"{tb_string}"
    )
    
    # Log detailed error (truncated to avoid massive logs)
    logger.error(error_message[:4000])
    
    # Only send error message to user if there's an update to respond to
    if update and update.effective_message:
        # Get error type for more specific messaging
        error_type = type(context.error).__name__
        
        # Generate user-friendly error message based on error type
        if "Unauthorized" in error_type:
            user_message = theme_engine.format_error_with_suggestion(
                "No tengo permisos suficientes para realizar esta acción.",
                "Asegúrate de que soy administrador del grupo con los permisos necesarios."
            )
        elif "BadRequest" in error_type:
            user_message = theme_engine.format_error_with_suggestion(
                "La solicitud no es válida.",
                "Verifica la sintaxis del comando y los parámetros."
            )
        elif "TimedOut" in error_type:
            user_message = theme_engine.format_error_with_suggestion(
                "La operación tardó demasiado tiempo.",
                "Inténtalo de nuevo más tarde cuando la red sea más estable."
            )
        elif "NetworkError" in error_type:
            user_message = theme_engine.format_error_with_suggestion(
                "Problemas de conexión con Telegram.",
                "Verifica tu conexión a internet e inténtalo de nuevo."
            )
        else:
            # Generic error message
            user_message = theme_engine.generate_message(MessageType.ERROR)
        
        # Send error message to user
        await update.effective_message.reply_text(
            user_message,
            parse_mode=ParseMode.MARKDOWN
        )


def register_error_handler(application):
    """
    Register the error handler with the application
    
    Args:
        application: Telegram bot application instance
    """
    application.add_error_handler(error_handler)
    logger.info("Error handler registered successfully")