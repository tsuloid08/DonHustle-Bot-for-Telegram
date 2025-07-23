#!/usr/bin/env python3
"""
@donhustle_bot - Simplified version to test functionality
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application, Defaults
from telegram.constants import ParseMode

# Fix Windows event loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Import handlers
from handlers import register_command_handlers, register_error_handler, register_welcome_handlers, register_moderation_handlers
from handlers.message_handler import register_message_handlers
from database.manager import get_database_manager, close_database
from utils.theme import ThemeEngine, ToneStyle

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

def initialize_bot():
    """Initialize the bot with all necessary components"""
    # Get bot token from environment variable
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not found!")
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
        
        logger.info("@donhustle_bot initialized successfully")
        return application
        
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        logger.exception("Initialization error details:")
        return None

def setup_handlers(application):
    """Set up all handlers for the bot application"""
    # Create theme engine for handlers
    theme_engine = ThemeEngine(ToneStyle.SERIOUS)
    
    # Store theme engine reference in application for access by handlers
    application.bot_data['theme_engine'] = theme_engine
    
    # Register command handlers
    command_handler = register_command_handlers(application)
    
    # Register message handlers for automatic quotes
    register_message_handlers(application, theme_engine)
    
    # Register welcome handlers
    register_welcome_handlers(application)
    
    # Register moderation handlers
    register_moderation_handlers(application, theme_engine)
    
    # Register error handler
    register_error_handler(application)
    
    # Skip scheduler for now to avoid event loop issues
    logger.info("All handlers registered successfully (scheduler disabled)")
    return command_handler

async def main():
    """Main function to initialize and run the bot"""
    application = None
    try:
        # Initialize the bot
        application = initialize_bot()
        
        if not application:
            logger.error("Bot initialization failed. Exiting.")
            return
        
        # Set up all handlers
        command_handler = setup_handlers(application)
        
        # Load custom commands asynchronously
        if command_handler:
            try:
                await command_handler.load_and_register_custom_commands(application)
            except Exception as e:
                logger.error(f"Error loading custom commands: {e}")
        
        # Test bot connection first
        try:
            bot_info = await application.bot.get_me()
            logger.info(f"Bot connected successfully: @{bot_info.username}")
        except Exception as e:
            logger.error(f"Failed to connect to bot: {e}")
            return
        
        # Log startup information
        logger.info("Starting @donhustle_bot...")
        
        # Start the bot with appropriate update types
        allowed_updates = [
            "message", 
            "edited_message", 
            "callback_query", 
            "chat_member"
        ]
        
        logger.info(f"Starting bot polling with updates: {', '.join(allowed_updates)}")
        
        # Use close_loop=False to let asyncio.run handle the event loop
        await application.run_polling(
            allowed_updates=allowed_updates,
            close_loop=False
        )
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.exception("Error details:")
    finally:
        # Properly shutdown the application
        if application:
            try:
                await application.shutdown()
                logger.info("Application shutdown complete")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        
        # Ensure database is closed
        close_database()
        logger.info("Bot shutdown complete")

if __name__ == '__main__':
    asyncio.run(main())