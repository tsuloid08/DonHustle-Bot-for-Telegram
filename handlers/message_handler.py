"""
Message handler for @donhustle_bot
Handles regular messages for counting, filtering, and automated responses
"""

import logging
from typing import Optional

from telegram import Update, Message
from telegram.ext import ContextTypes, MessageHandler, filters

from utils.theme import ThemeEngine, MessageType, ToneStyle
from database.manager import get_database_manager
from database.repositories import ConfigRepository, QuoteRepository, UserActivityRepository

logger = logging.getLogger(__name__)


class BotMessageHandler:
    """
    Handles regular messages for automatic quote sending and user activity tracking
    """
    
    def __init__(self, theme_engine: ThemeEngine):
        """
        Initialize the message handler
        
        Args:
            theme_engine: ThemeEngine instance for mafia-themed responses
        """
        self.theme_engine = theme_engine
        self.db_manager = get_database_manager()
        self.config_repository = ConfigRepository(self.db_manager)
        self.quote_repository = QuoteRepository(self.db_manager)
        self.user_activity_repository = UserActivityRepository(self.db_manager)
    
    async def check_and_send_interval_quote(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Check if it's time to send an interval quote and send it if needed
        
        Args:
            chat_id: Chat ID to check
            context: Telegram context for sending messages
        """
        try:
            # Get current message count and interval
            current_count = int(self.config_repository.get_config(chat_id, "message_count", "0"))
            interval = int(self.config_repository.get_config(chat_id, "quote_interval", "50"))
            
            # Increment message count
            new_count = current_count + 1
            self.config_repository.set_config(chat_id, "message_count", str(new_count))
            
            # Check if we've reached the interval
            if new_count >= interval:
                # Reset counter
                self.config_repository.set_config(chat_id, "message_count", "0")
                
                # Get a random quote
                quote_obj = self.quote_repository.get_random_quote()
                
                if quote_obj:
                    # Format the quote with mafia theming
                    formatted_quote = self.theme_engine.format_quote_message(quote_obj.quote)
                    
                    # Add interval message prefix
                    if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                        prefix = "⏰ *MOMENTO DE REFLEXIÓN*\n\nLa familia ha trabajado duro. Es hora de una dosis de sabiduría:\n\n"
                    else:
                        prefix = "⏰ *¡ALARMA DE MOTIVACIÓN!*\n\n¡La familia ha estado activa! Tiempo de inspiración:\n\n"
                    
                    final_message = prefix + formatted_quote
                    
                    # Send the quote
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=final_message,
                        parse_mode="Markdown"
                    )
                    
                    logger.info(f"Sent interval quote to chat {chat_id} after {interval} messages")
                
        except Exception as e:
            logger.error(f"Error checking/sending interval quote: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle regular messages for counting and automatic quote sending
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        message = update.effective_message
        chat = update.effective_chat
        user = update.effective_user
        
        if not message or not chat or not user:
            return
        
        # Skip bot messages and commands
        if user.is_bot or (message.text and message.text.startswith('/')):
            return
        
        # Only process group messages for automatic quotes
        if chat.type not in ["group", "supergroup"]:
            return
        
        try:
            # Update user activity
            self.user_activity_repository.update_user_activity(user.id, chat.id)
            
            # Check if we should send an interval quote
            await self.check_and_send_interval_quote(chat.id, context)
            
        except Exception as e:
            logger.error(f"Error processing message in chat {chat.id}: {e}")
    
    async def handle_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle new members joining the group
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        message = update.effective_message
        chat = update.effective_chat
        
        if not message or not chat or not message.new_chat_members:
            return
        
        try:
            # Get custom welcome message if configured
            welcome_message = self.config_repository.get_config(
                chat.id, 
                "welcome_message", 
                None
            )
            
            for new_member in message.new_chat_members:
                if new_member.is_bot:
                    continue
                
                if welcome_message:
                    # Use custom welcome message
                    formatted_welcome = welcome_message.replace("{name}", new_member.first_name)
                else:
                    # Use default mafia-themed welcome
                    formatted_welcome = self.theme_engine.generate_message(
                        MessageType.WELCOME,
                        name=new_member.first_name
                    )
                    formatted_welcome += "\n\nUsa /rules para conocer las reglas de la familia."
                
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=formatted_welcome,
                    parse_mode="Markdown"
                )
                
                # Initialize user activity
                self.user_activity_repository.update_user_activity(new_member.id, chat.id)
                
        except Exception as e:
            logger.error(f"Error handling new member in chat {chat.id}: {e}")


def register_message_handlers(application, theme_engine: ThemeEngine):
    """
    Register message handlers with the application
    
    Args:
        application: Telegram bot application instance
        theme_engine: ThemeEngine instance
    """
    # Create message handler
    message_handler = BotMessageHandler(theme_engine)
    
    # Register regular message handler (excluding commands)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler.handle_message
        )
    )
    
    # Register new member handler
    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            message_handler.handle_new_member
        )
    )
    
    logger.info("Message handlers registered successfully")