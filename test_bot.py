#!/usr/bin/env python3
"""
Simple test bot to verify basic functionality
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fix Windows event loop policy
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def start(update, context):
    """Handle /start command"""
    await update.message.reply_text(
        "¡Bienvenido a la familia, capo! 🤝\n\n"
        "Soy @donhustlebot, tu asistente mafioso para el éxito.\n\n"
        "Usa /help para ver los comandos disponibles."
    )

async def help_command(update, context):
    """Handle /help command"""
    help_text = """
🔫 *COMANDOS DE LA FAMILIA* 🔫

/start - Mensaje de bienvenida
/help - Mostrar esta ayuda
/hustle - Recibir motivación

_La familia siempre está aquí para ayudarte, capo._
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def hustle(update, context):
    """Handle /hustle command"""
    quotes = [
        "El éxito no es definitivo, el fracaso no es fatal: lo que cuenta es el coraje para continuar.",
        "No cuentes los días, haz que los días cuenten.",
        "La mejor manera de predecir el futuro es crearlo.",
        "El trabajo duro vence al talento cuando el talento no trabaja duro."
    ]
    import random
    quote = random.choice(quotes)
    
    formatted_quote = f"💪 *MOTIVACIÓN DE LA FAMILIA* 💪\n\n\"{quote}\"\n\n_— Don Hustle_"
    await update.message.reply_text(formatted_quote, parse_mode='Markdown')

async def main():
    """Main function"""
    # Get bot token from .env file
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        logger.error("BOT_TOKEN not found in .env file!")
        logger.error("Make sure your .env file contains: BOT_TOKEN=8056905769:AAEOPwkN2eBk5XDt999MSxyKU1MB6PYaSKU")
        return
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("hustle", hustle))
    
    logger.info("Test bot handlers registered")
    
    try:
        # Test connection
        bot_info = await application.bot.get_me()
        logger.info(f"Bot connected successfully: @{bot_info.username}")
        
        logger.info("Starting test bot...")
        
        # Start polling with close_loop=False
        await application.run_polling(
            allowed_updates=["message"],
            close_loop=False
        )
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.exception("Error details:")
    finally:
        # Proper shutdown
        try:
            await application.shutdown()
            logger.info("Bot shutdown complete")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")

if __name__ == "__main__":
    asyncio.run(main())