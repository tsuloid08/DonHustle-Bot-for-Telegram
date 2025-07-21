"""
Welcome message handler for @donhustle_bot
Implements welcome message configuration and new member detection
"""

import logging
from typing import Optional

from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.theme import ThemeEngine, MessageType
from database.manager import get_database_manager
from database.repositories import ConfigRepository

logger = logging.getLogger(__name__)

# Global theme engine instance
theme_engine = ThemeEngine()


async def handle_welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /welcome command to configure welcome messages
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    chat = update.effective_chat
    user = update.effective_user
    
    if not chat or not user:
        return
    
    # Check if user is admin in group chat
    is_admin = False
    if chat.type != "private":
        try:
            chat_member = await context.bot.get_chat_member(chat.id, user.id)
            is_admin = chat_member.status in ["creator", "administrator"]
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
    
    # Only allow admins to set welcome message in groups
    if chat.type != "private" and not is_admin:
        await update.message.reply_text(
            theme_engine.format_error_with_suggestion(
                "No tienes permiso para configurar el mensaje de bienvenida.",
                "Solo los administradores pueden usar este comando."
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Get welcome message from command arguments
    welcome_message = " ".join(context.args) if context.args else None
    
    if not welcome_message:
        # No message provided, show current welcome message
        db_manager = get_database_manager()
        config_repo = ConfigRepository(db_manager)
        current_welcome = config_repo.get_config(chat.id, "welcome_message")
        
        if current_welcome:
            await update.message.reply_text(
                f"*Mensaje de bienvenida actual:*\n\n{current_welcome}\n\n"
                "Para cambiar el mensaje, usa `/welcome [nuevo mensaje]`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # Show default welcome message
            default_welcome = get_default_welcome_message()
            await update.message.reply_text(
                f"*Mensaje de bienvenida predeterminado:*\n\n{default_welcome}\n\n"
                "Para configurar un mensaje personalizado, usa `/welcome [mensaje]`",
                parse_mode=ParseMode.MARKDOWN
            )
        return
    
    # Save welcome message to database
    try:
        db_manager = get_database_manager()
        config_repo = ConfigRepository(db_manager)
        config_repo.set_config(chat.id, "welcome_message", welcome_message)
        
        success_message = theme_engine.generate_message(MessageType.SUCCESS)
        await update.message.reply_text(
            f"{success_message}\n\n*Nuevo mensaje de bienvenida configurado:*\n\n{welcome_message}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Welcome message set for chat {chat.id} by user {user.id}")
    except Exception as e:
        logger.error(f"Error setting welcome message: {e}")
        error_message = theme_engine.generate_message(MessageType.ERROR)
        await update.message.reply_text(
            f"{error_message}\n\nNo se pudo guardar el mensaje de bienvenida.",
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle chat member updates to detect new members
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    result = extract_status_change(update.chat_member)
    if not result:
        return
    
    was_member, is_member = result
    
    # Check if this is a new member joining
    if not was_member and is_member:
        await send_welcome_message(update, context)


async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send welcome message to new members
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    chat = update.effective_chat
    new_member = update.chat_member.new_chat_member.user if update.chat_member else None
    
    if not chat or not new_member:
        return
    
    # Skip welcome message for the bot itself
    if new_member.id == context.bot.id:
        return
    
    try:
        # Get custom welcome message from database
        db_manager = get_database_manager()
        config_repo = ConfigRepository(db_manager)
        welcome_message = config_repo.get_config(chat.id, "welcome_message")
        
        # Use default welcome message if none configured
        if not welcome_message:
            welcome_message = get_default_welcome_message()
        
        # Replace placeholders in welcome message
        welcome_message = welcome_message.replace("{name}", new_member.first_name)
        welcome_message = welcome_message.replace("{username}", f"@{new_member.username}" if new_member.username else new_member.first_name)
        welcome_message = welcome_message.replace("{chat}", chat.title or "grupo")
        
        # Add mafia-themed enhancement
        welcome_message = theme_engine.enhance_message(welcome_message, add_phrase=True)
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Welcome message sent for new member {new_member.id} in chat {chat.id}")
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")


def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[tuple[bool, bool]]:
    """
    Extract status change from chat member update
    
    Args:
        chat_member_update: ChatMemberUpdated object
        
    Returns:
        Tuple of (was_member, is_member) or None if no status change
    """
    if not chat_member_update:
        return None
    
    # Get previous and current status
    old_status = chat_member_update.old_chat_member.status
    new_status = chat_member_update.new_chat_member.status
    
    # Check if user was a member before
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR
    ]
    
    # Check if user is a member now
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR
    ]
    
    return was_member, is_member


def get_default_welcome_message() -> str:
    """
    Get default mafia-themed welcome message
    
    Returns:
        Default welcome message text
    """
    return (
        "¡Bienvenido a la familia, {name}! 🤝\n\n"
        "Aquí trabajamos duro y respetamos el negocio. Sigue las reglas, "
        "muestra lealtad a la familia, y prosperaremos juntos.\n\n"
        "Usa /rules para ver las reglas de la familia."
    )


def register_welcome_handlers(application):
    """
    Register welcome message handlers with the application
    
    Args:
        application: Telegram bot application instance
    """
    from telegram.ext import CommandHandler, ChatMemberHandler
    
    # Register welcome command handler
    application.add_handler(CommandHandler("welcome", handle_welcome_command))
    
    # Register chat member update handler for new member detection
    application.add_handler(ChatMemberHandler(handle_chat_member_update))
    
    logger.info("Welcome handlers registered successfully")