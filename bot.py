#!/usr/bin/env python3
"""
@donhustle_bot - Telegram Bot with Mafia Theme
Main application entry point
"""

import os
import sys
import logging
from dotenv import load_dotenv
from telegram.ext import Application, Defaults
from telegram.constants import ParseMode

# Import handlers
from handlers import register_command_handlers, register_error_handler, register_welcome_handlers, register_moderation_handlers
from handlers.message_handler import register_message_handlers
from database.manager import get_database_manager, close_database
from utils.theme import ThemeEngine, ToneStyle
from utils.scheduler import setup_scheduler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)


async def setup_handlers(application):
    """
    Set up all handlers for the bot application
    
    Args:
        application: Telegram bot application instance
    """
    # Create theme engine for handlers
    theme_engine = ThemeEngine(ToneStyle.SERIOUS)
    
    # Register command handlers
    command_handler = register_command_handlers(application)
    
    # Load and register existing custom commands
    if command_handler:
        await command_handler.load_and_register_custom_commands(application)
    
    # Register message handlers for automatic quotes
    register_message_handlers(application, theme_engine)
    
    # Register welcome handlers
    register_welcome_handlers(application)
    
    # Register moderation handlers
    register_moderation_handlers(application, theme_engine)
    
    # Register error handler
    register_error_handler(application)
    
    # Set up reminder scheduler
    setup_scheduler(application, theme_engine)
    
    logger.info("All handlers registered successfully")


def initialize_bot():
    """
    Initialize the bot with all necessary components
    
    Returns:
        Configured Application instance or None if initialization fails
    """
    # Get bot token from environment variable
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not found!")
        logger.error("Please create a .env file with your bot token:")
        logger.error("BOT_TOKEN=your_actual_bot_token_here")
        logger.error("Get your token from @BotFather on Telegram")
        return None
    
    # Validate token format (basic check)
    if not bot_token.count(':') == 1 or len(bot_token) < 35:
        logger.error("Invalid BOT_TOKEN format! Token should be like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        return None
    
    try:
        # Initialize database
        db_path = os.getenv('DATABASE_PATH', 'bot_database.db')
        db_manager = get_database_manager(db_path)
        logger.info(f"Database initialized at {db_path}")
        
        # Set default parse mode for all messages
        defaults = Defaults(parse_mode=ParseMode.MARKDOWN)
        
        # Create application with defaults
        application = Application.builder().token(bot_token).defaults(defaults).build()
        
        # Set up all handlers (this needs to be done after the application is created)
        # We'll set up handlers in the main function after the application is ready
        
        logger.info("@donhustle_bot initialized successfully")
        return application
        
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        logger.exception("Initialization error details:")
        return None


async def main():
    """Main function to initialize and run the bot"""
    try:
        # Initialize the bot
        application = initialize_bot()
        
        if not application:
            logger.error("Bot initialization failed. Exiting.")
            return
        
        # Set up all handlers (including loading custom commands)
        await setup_handlers(application)
        
        # Log startup information
        logger.info("Starting @donhustle_bot...")
        
        # Register shutdown handler
        application.post_shutdown = close_database
        
        # Start the bot with appropriate update types
        allowed_updates = [
            "message", 
            "edited_message", 
            "callback_query", 
            "chat_member"
        ]
        
        logger.info(f"Starting bot polling with updates: {', '.join(allowed_updates)}")
        await application.run_polling(allowed_updates=allowed_updates)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.exception("Error details:")
    finally:
        # Ensure database is closed
        close_database()
        logger.info("Bot shutdown complete")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())