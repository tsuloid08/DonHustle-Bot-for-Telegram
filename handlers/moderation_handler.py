"""
Moderation handler for @donhustle_bot
Implements spam detection and moderation features with mafia-themed responses
"""

import logging
from typing import Dict, List, Optional, Tuple
import re

from telegram import Update, User, Chat
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

from utils.theme import ThemeEngine, MessageType, ToneStyle
from database.manager import get_database_manager
from database.repositories import SpamFilterRepository, ConfigRepository
from database.models import SpamFilter

logger = logging.getLogger(__name__)


class ModerationHandler:
    """
    Handles spam detection and moderation features with mafia-themed responses
    """
    
    def __init__(self, theme_engine: ThemeEngine):
        """
        Initialize the moderation handler
        
        Args:
            theme_engine: ThemeEngine instance for mafia-themed responses
        """
        self.theme_engine = theme_engine
        self.db_manager = get_database_manager()
        self.spam_filter_repository = SpamFilterRepository(self.db_manager)
        self.config_repository = ConfigRepository(self.db_manager)
        
        # User strike system - tracks warnings per user
        # Format: {chat_id: {user_id: strike_count}}
        self.user_strikes: Dict[int, Dict[int, int]] = {}
    
    async def check_admin_permissions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Check if user has admin permissions in the chat
        
        Args:
            update: Telegram update object
            context: Telegram context object
            
        Returns:
            True if user is admin, False otherwise
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return False
        
        # Private chats - user is always admin
        if chat.type == "private":
            return True
        
        try:
            chat_member = await context.bot.get_chat_member(chat.id, user.id)
            return chat_member.status in ["creator", "administrator"]
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False
    
    async def handle_filter_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /filter add command - add a new spam filter word
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Check admin permissions
        if not await self.check_admin_permissions(update, context):
            warning_message = self.theme_engine.generate_message(
                MessageType.WARNING,
                name=update.effective_user.first_name if update.effective_user else "capo"
            )
            await update.message.reply_text(
                f"{warning_message}\n\nSolo los administradores pueden configurar filtros de spam.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Check if command has arguments
        if not context.args or len(context.args) < 1:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "No especificaste la palabra a filtrar",
                "Usa /filter add [palabra] para agregar una palabra al filtro"
            )
            await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Get filter word and optional action
        filter_word = context.args[0].lower()
        action = "warn"  # Default action
        
        if len(context.args) >= 2:
            action_arg = context.args[1].lower()
            if action_arg in ["warn", "delete", "ban"]:
                action = action_arg
        
        # Add filter to database
        try:
            chat_id = update.effective_chat.id
            filter_id = self.spam_filter_repository.add_spam_filter(chat_id, filter_word, action)
            
            if filter_id:
                success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                
                if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                    filter_message = f"Palabra filtrada: *{filter_word}*\nAcción: *{action}*"
                else:
                    filter_message = f"¡Palabra prohibida añadida! Quien diga *{filter_word}* estará nadando con tiburones.\nAcción: *{action}*"
                
                await update.message.reply_text(
                    f"{success_message}\n\n{filter_message}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(
                    f"{error_message}\n\nNo se pudo agregar el filtro.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Error adding spam filter: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_filter_remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /filter remove command - remove a spam filter word
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Check admin permissions
        if not await self.check_admin_permissions(update, context):
            warning_message = self.theme_engine.generate_message(
                MessageType.WARNING,
                name=update.effective_user.first_name if update.effective_user else "capo"
            )
            await update.message.reply_text(
                f"{warning_message}\n\nSolo los administradores pueden configurar filtros de spam.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Check if command has arguments
        if not context.args or len(context.args) < 1:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "No especificaste la palabra a eliminar",
                "Usa /filter remove [palabra] para eliminar una palabra del filtro"
            )
            await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Get filter word
        filter_word = context.args[0].lower()
        
        # Remove filter from database
        try:
            chat_id = update.effective_chat.id
            removed = self.spam_filter_repository.remove_spam_filter(chat_id, filter_word)
            
            if removed:
                success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                
                if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                    filter_message = f"Palabra eliminada del filtro: *{filter_word}*"
                else:
                    filter_message = f"¡Palabra liberada! *{filter_word}* ya no está en la lista negra."
                
                await update.message.reply_text(
                    f"{success_message}\n\n{filter_message}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                error_message = self.theme_engine.generate_message(MessageType.WARNING)
                await update.message.reply_text(
                    f"{error_message}\n\nLa palabra *{filter_word}* no estaba en el filtro.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Error removing spam filter: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_filter_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /filter list command - show all spam filter words
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Check admin permissions
        if not await self.check_admin_permissions(update, context):
            warning_message = self.theme_engine.generate_message(
                MessageType.WARNING,
                name=update.effective_user.first_name if update.effective_user else "capo"
            )
            await update.message.reply_text(
                f"{warning_message}\n\nSolo los administradores pueden ver los filtros de spam.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Get all filters for this chat
        try:
            chat_id = update.effective_chat.id
            filters = self.spam_filter_repository.get_spam_filters(chat_id)
            
            if not filters:
                warning_message = self.theme_engine.generate_message(
                    MessageType.WARNING,
                    name="capo"
                )
                await update.message.reply_text(
                    f"{warning_message}\n\nNo hay palabras en el filtro de spam.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Format filters list with mafia theming
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                header = "📋 *LISTA DE PALABRAS PROHIBIDAS* 📋\n\nLa familia no tolera estas palabras:"
            else:
                header = "📋 *LISTA NEGRA DE LA FAMILIA* 📋\n\n¡Estas palabras te harán nadar con tiburones!"
            
            filter_lines = []
            for i, spam_filter in enumerate(filters, 1):
                filter_lines.append(f"{i}. *{spam_filter.filter_word}* (Acción: {spam_filter.action})")
            
            filters_text = "\n".join(filter_lines)
            footer = f"\n\n_Total: {len(filters)} palabras prohibidas_"
            
            await update.message.reply_text(
                f"{header}\n\n{filters_text}{footer}",
                parse_mode=ParseMode.MARKDOWN
            )
                
        except Exception as e:
            logger.error(f"Error listing spam filters: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_filter_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /filter command - main entry point for filter commands
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        if not context.args:
            # Show help for filter command
            help_text = """
📋 *COMANDOS DE FILTRO DE SPAM* 📋

Usa estos comandos para gestionar el filtro de spam:

/filter add [palabra] - Agregar palabra al filtro
/filter remove [palabra] - Eliminar palabra del filtro
/filter list - Ver todas las palabras filtradas

_Ejemplo: /filter add spam_
            """
            await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Route to appropriate subcommand
        subcommand = context.args[0].lower()
        
        # Remove the subcommand from args
        context.args = context.args[1:]
        
        if subcommand == "add":
            await self.handle_filter_add(update, context)
        elif subcommand == "remove":
            await self.handle_filter_remove(update, context)
        elif subcommand == "list":
            await self.handle_filter_list(update, context)
        else:
            error_msg = self.theme_engine.format_error_with_suggestion(
                f"Subcomando desconocido: {subcommand}",
                "Usa /filter add, /filter remove o /filter list"
            )
            await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)
    
    def get_user_strikes(self, chat_id: int, user_id: int) -> int:
        """
        Get the number of strikes for a user
        
        Args:
            chat_id: Chat ID
            user_id: User ID
            
        Returns:
            Number of strikes
        """
        if chat_id not in self.user_strikes:
            self.user_strikes[chat_id] = {}
        
        return self.user_strikes[chat_id].get(user_id, 0)
    
    def add_user_strike(self, chat_id: int, user_id: int) -> int:
        """
        Add a strike to a user
        
        Args:
            chat_id: Chat ID
            user_id: User ID
            
        Returns:
            New strike count
        """
        if chat_id not in self.user_strikes:
            self.user_strikes[chat_id] = {}
        
        current_strikes = self.user_strikes[chat_id].get(user_id, 0)
        new_strikes = current_strikes + 1
        self.user_strikes[chat_id][user_id] = new_strikes
        
        return new_strikes
    
    async def check_spam_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Check if a message contains spam and take appropriate action
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        message = update.effective_message
        chat = update.effective_chat
        user = update.effective_user
        
        if not message or not chat or not user or not message.text:
            return
        
        # Skip bot messages and commands
        if user.is_bot or message.text.startswith('/'):
            return
        
        try:
            # Check if message contains spam
            spam_filter = self.spam_filter_repository.check_spam(chat.id, message.text)
            
            if spam_filter:
                # Log the spam detection
                logger.info(f"Spam detected in chat {chat.id} from user {user.id}: {spam_filter.filter_word}")
                
                # Take action based on filter configuration
                action = spam_filter.action
                
                if action == "delete":
                    # Delete the message
                    await message.delete()
                    
                    # Send warning
                    warning_message = self.theme_engine.generate_message(
                        MessageType.WARNING,
                        name=user.first_name
                    )
                    
                    if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                        action_message = f"Tu mensaje ha sido eliminado por contener palabras prohibidas."
                    else:
                        action_message = f"¡Cuidado con lo que dices! Estás nadando con tiburones. Mensaje eliminado."
                    
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=f"{warning_message}\n\n{action_message}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                elif action == "warn":
                    # Add a strike
                    strikes = self.add_user_strike(chat.id, user.id)
                    
                    # Send warning
                    warning_message = self.theme_engine.generate_message(
                        MessageType.WARNING,
                        name=user.first_name
                    )
                    
                    if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                        action_message = f"Has usado una palabra prohibida. Advertencia {strikes}/3."
                    else:
                        action_message = f"¡Estás nadando con tiburones! Advertencia {strikes}/3. Ten cuidado con tus palabras."
                    
                    await message.reply_text(
                        f"{warning_message}\n\n{action_message}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    # If user has 3 strikes, take additional action
                    if strikes >= 3:
                        if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                            final_warning = f"Has alcanzado el límite de advertencias. La próxima vez serás expulsado."
                        else:
                            final_warning = f"¡Tres strikes! La próxima vez dormirás con los peces. Última advertencia."
                        
                        await context.bot.send_message(
                            chat_id=chat.id,
                            text=f"⚠️ *ÚLTIMA ADVERTENCIA* ⚠️\n\n{user.mention_markdown()}: {final_warning}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                        # Reset strikes
                        self.user_strikes[chat.id][user.id] = 0
                
                elif action == "ban":
                    # Ban the user
                    try:
                        await context.bot.ban_chat_member(chat.id, user.id)
                        
                        ban_message = self.theme_engine.generate_message(
                            MessageType.WARNING,
                            name=user.first_name
                        )
                        
                        if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                            action_message = f"{user.mention_markdown()} ha sido expulsado por usar palabras prohibidas."
                        else:
                            action_message = f"{user.mention_markdown()} ha ido a dormir con los peces por no respetar las reglas de la familia."
                        
                        await context.bot.send_message(
                            chat_id=chat.id,
                            text=f"{ban_message}\n\n{action_message}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                    except Exception as e:
                        logger.error(f"Error banning user: {e}")
                        
                        error_message = self.theme_engine.generate_message(MessageType.ERROR)
                        await context.bot.send_message(
                            chat_id=chat.id,
                            text=f"{error_message}\n\nNo se pudo expulsar al usuario. Asegúrate de que el bot tenga permisos de administrador.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                
        except Exception as e:
            logger.error(f"Error checking spam: {e}")


def register_moderation_handlers(application, theme_engine: ThemeEngine):
    """
    Register moderation handlers with the application
    
    Args:
        application: Telegram bot application instance
        theme_engine: ThemeEngine instance
    """
    # Create moderation handler
    moderation_handler = ModerationHandler(theme_engine)
    
    # Register filter command
    application.add_handler(CommandHandler("filter", moderation_handler.handle_filter_command))
    
    # Register message handler for spam detection
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            moderation_handler.check_spam_message,
            group=1  # Higher group number means lower priority
        )
    )
    
    logger.info("Moderation handlers registered successfully")