"""
Command handlers for @donhustle_bot
Implements all bot commands with mafia-themed responses
"""

import logging
import inspect
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Type, Tuple
from abc import ABC, abstractmethod

from telegram import Update, Chat, User
from telegram.ext import ContextTypes, CommandHandler as TelegramCommandHandler
from telegram.constants import ParseMode

from utils.theme import ThemeEngine, MessageType, ToneStyle
from utils.file_processor import FileProcessor
from database.manager import get_database_manager
from database.repositories import (
    QuoteRepository, ConfigRepository, UserActivityRepository, 
    MessageRepository, ReminderRepository, CustomCommandRepository
)

logger = logging.getLogger(__name__)

# Global theme engine instance
theme_engine = ThemeEngine()


class BaseCommandHandler(ABC):
    """
    Abstract base class for command handlers with common functionality
    """
    
    def __init__(self, theme_engine: ThemeEngine):
        """
        Initialize the command handler
        
        Args:
            theme_engine: ThemeEngine instance for mafia-themed responses
        """
        self.theme_engine = theme_engine
    
    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the command
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        pass
    
    def get_command_name(self) -> str:
        """
        Get the command name from the class name
        
        Returns:
            Command name in lowercase
        """
        class_name = self.__class__.__name__
        if class_name.endswith("Command"):
            return class_name[:-7].lower()
        return class_name.lower()
    
    async def check_user_permissions(self, update: Update) -> bool:
        """
        Check if user has required permissions for the command
        
        Args:
            update: Telegram update object
            
        Returns:
            True if user has permissions, False otherwise
        """
        # Default implementation - override in subclasses for specific permission checks
        return True
    
    async def send_response(self, update: Update, message: str, **kwargs) -> None:
        """
        Send a response message with proper formatting
        
        Args:
            update: Telegram update object
            message: Message text to send
            **kwargs: Additional parameters for reply_text
        """
        if update.effective_message:
            parse_mode = kwargs.pop("parse_mode", ParseMode.MARKDOWN)
            await update.effective_message.reply_text(
                message,
                parse_mode=parse_mode,
                **kwargs
            )


class CommandHandler:
    """
    Main command handler class that manages all bot commands
    """
    
    def __init__(self, theme_engine: ThemeEngine):
        """
        Initialize the command handler
        
        Args:
            theme_engine: ThemeEngine instance for mafia-themed responses
        """
        self.theme_engine = theme_engine
        self.db_manager = get_database_manager()
        self.quote_repository = QuoteRepository(self.db_manager)
        self.config_repository = ConfigRepository(self.db_manager)
        self.user_activity_repository = UserActivityRepository(self.db_manager)
        self.message_repository = MessageRepository(self.db_manager)
        self.reminder_repository = ReminderRepository(self.db_manager)
        self.custom_command_repository = CustomCommandRepository(self.db_manager)
        self.file_processor = FileProcessor(self.theme_engine)
        self._command_registry = {}
    
    def _load_chat_style(self, chat_id: int) -> None:
        """
        Load and apply the bot style configuration for a specific chat
        
        Args:
            chat_id: Chat ID to load style for
        """
        try:
            style_config = self.config_repository.get_config(chat_id, "bot_style", "serio")
            
            if style_config == "humorístico":
                self.theme_engine.set_tone(ToneStyle.HUMOROUS)
            else:
                self.theme_engine.set_tone(ToneStyle.SERIOUS)
                
        except Exception as e:
            logger.error(f"Error loading chat style for {chat_id}: {e}")
            # Default to serious tone on error
            self.theme_engine.set_tone(ToneStyle.SERIOUS)
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command - introduction and help information
        """
        user = update.effective_user
        chat = update.effective_chat
        
        if not user or not chat:
            return
        
        # Load chat-specific style configuration
        self._load_chat_style(chat.id)
        
        # Different welcome for private vs group chats
        if chat.type == "private":
            welcome_message = self.theme_engine.generate_message(
                MessageType.WELCOME, 
                name=user.first_name
            )
            
            commands = {
                "start": "Mostrar este mensaje de ayuda",
                "rules": "Ver las reglas de la familia",
                "hustle": "Recibir una frase motivacional",
                "help": "Mostrar comandos disponibles"
            }
            
            help_text = self.theme_engine.format_command_help(commands)
            
            await update.message.reply_text(
                f"{welcome_message}\n\n{help_text}",
                parse_mode="Markdown"
            )
        else:
            # Group chat welcome
            welcome_message = self.theme_engine.generate_message(
                MessageType.WELCOME, 
                name=user.first_name
            )
            
            await update.message.reply_text(
                f"{welcome_message}\n\nUsa /help para ver los comandos disponibles.",
                parse_mode="Markdown"
            )
    
    async def handle_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /rules command - display group rules with hustle culture principles
        """
        chat_id = update.effective_chat.id if update.effective_chat else None
        
        if chat_id:
            # Load chat-specific style configuration
            self._load_chat_style(chat_id)
        
        # Try to get custom rules from database if available
        custom_rules = None
        if chat_id:
            try:
                with self.db_manager.get_cursor() as cursor:
                    cursor.execute(
                        "SELECT value FROM config WHERE chat_id = ? AND key = 'rules'",
                        (chat_id,)
                    )
                    result = cursor.fetchone()
                    if result:
                        custom_rules = result[0].split('\n')
            except Exception as e:
                logger.error(f"Error fetching custom rules: {e}")
        
        # Use default rules if no custom rules found
        if not custom_rules:
            rules = [
                "1️⃣ *Trabaja duro* - La familia valora el esfuerzo y la dedicación",
                "2️⃣ *Sin spam* - Respeta el espacio de la familia",
                "3️⃣ *Lealtad al negocio* - Apoya a tus compañeros",
                "4️⃣ *Respeto* - Trata a todos con respeto y dignidad",
                "5️⃣ *Ambición* - Busca siempre mejorar y crecer"
            ]
        else:
            rules = custom_rules
        
        # Mafia-themed rules header
        if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
            rules_header = "📜 *REGLAS DE LA FAMILIA* 📜\n\nEstas reglas no se negocian, capo. Respétalas."
        else:
            rules_header = "📜 *REGLAS DE LA FAMILIA* 📜\n\n¿Quieres ser parte de la familia? Sigue estas reglas o dormirás con los peces."
        
        rules_text = f"{rules_header}\n\n" + "\n\n".join(rules)
        
        # Add iconic phrase as footer
        rules_footer = f"\n\n_{self.theme_engine.get_iconic_phrase()}_"
        
        await update.message.reply_text(
            rules_text + rules_footer,
            parse_mode="Markdown"
        )
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /help command - show available commands
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
        
        # Different command sets for private vs group chats
        if chat.type == "private":
            commands = {
                "start": "Mostrar mensaje de bienvenida",
                "rules": "Ver las reglas de la familia",
                "hustle": "Recibir una frase motivacional",
                "help": "Mostrar este mensaje de ayuda"
            }
        else:
            # Basic group commands for all users
            commands = {
                "rules": "Ver las reglas del grupo",
                "hustle": "Recibir una frase motivacional",
                "help": "Mostrar este mensaje de ayuda"
            }
            
            # Add admin commands if user is admin
            if is_admin:
                admin_commands = {
                    "welcome": "Configurar mensaje de bienvenida para nuevos miembros",
                    "uploadquotes": "Subir archivo con frases (.txt, .csv, .json)",
                    "setquoteinterval": "Configurar frecuencia de frases",
                    "setstyle": "Ajustar tono del bot (serio/humorístico)",
                    "listquotes": "Ver todas las frases motivacionales",
                    "addhustle": "Agregar una nueva frase motivacional",
                    "deletequote": "Eliminar una frase específica por número",
                    "clearquotes": "Eliminar todas las frases (requiere confirmación)",
                    "addcommand": "Crear comando personalizado (/addcommand [nombre] [respuesta])",
                    "customcommands": "Ver todos los comandos personalizados",
                    "deletecommand": "Eliminar comando personalizado"
                }
                commands.update(admin_commands)
            
            # Add reminder commands for all users
            reminder_commands = {
                "remind": "Programar un recordatorio (ej: /remind tomorrow 15:00 Reunión)",
                "remind weekly": "Programar recordatorio semanal (ej: /remind weekly monday 10:00 Informe)",
                "reminders": "Ver todos los recordatorios activos"
            }
            commands.update(reminder_commands)
        
        help_text = self.theme_engine.format_command_help(commands)
        
        await update.message.reply_text(
            help_text,
            parse_mode="Markdown"
        )
    
    async def handle_hustle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /hustle command - send a motivational quote
        """
        # Try to get a random quote from the database
        quote = None
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT quote FROM quotes ORDER BY RANDOM() LIMIT 1")
                result = cursor.fetchone()
                if result:
                    quote = result[0]
        except Exception as e:
            logger.error(f"Error fetching quote: {e}")
        
        # Use default quote if none found in database
        if not quote:
            default_quotes = [
                "El éxito no es definitivo, el fracaso no es fatal: lo que cuenta es el coraje para continuar.",
                "No cuentes los días, haz que los días cuenten.",
                "La mejor manera de predecir el futuro es crearlo.",
                "El trabajo duro vence al talento cuando el talento no trabaja duro.",
                "No hay ascensores hacia el éxito, hay que tomar las escaleras."
            ]
            quote = default_quotes[hash(update.effective_user.id) % len(default_quotes) if update.effective_user else 0]
        
        # Format the quote with mafia theming
        formatted_quote = self.theme_engine.format_quote_message(quote)
        
        await update.message.reply_text(
            formatted_quote,
            parse_mode="Markdown"
        )
    
    async def handle_listquotes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /listquotes command - show all quotes with indices
        """
        try:
            quotes = self.quote_repository.get_all_quotes()
            
            if not quotes:
                no_quotes_message = self.theme_engine.generate_message(
                    MessageType.WARNING,
                    name="capo"
                )
                await update.message.reply_text(
                    f"{no_quotes_message}\n\nNo hay frases en el libro de la familia. Usa /addhustle para agregar una.",
                    parse_mode="Markdown"
                )
                return
            
            # Format quotes list with mafia theming
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                header = "📚 *LIBRO DE FRASES DE LA FAMILIA* 📚\n\nSabiduría acumulada por la organización:"
            else:
                header = "📚 *ARSENAL DE MOTIVACIÓN MAFIOSA* 📚\n\n¡Aquí están todas las joyas de sabiduría!"
            
            quote_lines = []
            for i, quote in enumerate(quotes, 1):
                # Truncate long quotes for display
                display_quote = quote.quote
                if len(display_quote) > 100:
                    display_quote = display_quote[:97] + "..."
                quote_lines.append(f"{i}. {display_quote}")
            
            # Split into chunks if too many quotes
            max_quotes_per_message = 20
            if len(quote_lines) <= max_quotes_per_message:
                quotes_text = "\n\n".join(quote_lines)
                footer = f"\n\n_Total: {len(quotes)} frases en el archivo de la familia_"
                
                await update.message.reply_text(
                    f"{header}\n\n{quotes_text}{footer}",
                    parse_mode="Markdown"
                )
            else:
                # Send in chunks
                for i in range(0, len(quote_lines), max_quotes_per_message):
                    chunk = quote_lines[i:i + max_quotes_per_message]
                    chunk_text = "\n\n".join(chunk)
                    
                    if i == 0:
                        message = f"{header}\n\n{chunk_text}"
                    else:
                        message = f"📚 *Continuación...* 📚\n\n{chunk_text}"
                    
                    if i + max_quotes_per_message >= len(quote_lines):
                        message += f"\n\n_Total: {len(quotes)} frases en el archivo de la familia_"
                    
                    await update.message.reply_text(message, parse_mode="Markdown")
                    
        except Exception as e:
            logger.error(f"Error listing quotes: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_deletequote(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /deletequote command - remove specific quote by index
        """
        if not context.args:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "No especificaste qué frase eliminar",
                "Usa /deletequote [número] para eliminar una frase específica"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        try:
            quote_index = int(context.args[0])
            
            # Get all quotes to find the one at the specified index
            quotes = self.quote_repository.get_all_quotes()
            
            if not quotes:
                warning_message = self.theme_engine.generate_message(
                    MessageType.WARNING,
                    name="capo"
                )
                await update.message.reply_text(
                    f"{warning_message}\n\nNo hay frases para eliminar en el archivo de la familia.",
                    parse_mode="Markdown"
                )
                return
            
            if quote_index < 1 or quote_index > len(quotes):
                error_msg = self.theme_engine.format_error_with_suggestion(
                    f"Número de frase inválido: {quote_index}",
                    f"Usa un número entre 1 y {len(quotes)}"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            # Get the quote to delete (quotes are ordered by ID DESC, so we need to get the right one)
            quote_to_delete = quotes[quote_index - 1]
            
            # Delete the quote
            if self.quote_repository.delete_quote(quote_to_delete.id):
                success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                quote_preview = quote_to_delete.quote[:50] + "..." if len(quote_to_delete.quote) > 50 else quote_to_delete.quote
                
                await update.message.reply_text(
                    f"{success_message}\n\n*Frase eliminada:* \"{quote_preview}\"",
                    parse_mode="Markdown"
                )
            else:
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(
                    f"{error_message}\n\nNo se pudo eliminar la frase del archivo.",
                    parse_mode="Markdown"
                )
                
        except ValueError:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "El número de frase debe ser un número válido",
                "Usa /deletequote [número] con un número entero"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error deleting quote: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_clearquotes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /clearquotes command - delete all quotes with confirmation
        """
        try:
            quotes = self.quote_repository.get_all_quotes()
            
            if not quotes:
                warning_message = self.theme_engine.generate_message(
                    MessageType.WARNING,
                    name="capo"
                )
                await update.message.reply_text(
                    f"{warning_message}\n\nNo hay frases para limpiar en el archivo de la familia.",
                    parse_mode="Markdown"
                )
                return
            
            # Check if this is a confirmation (user sends "confirmar" or "sí")
            if context.args and context.args[0].lower() in ["confirmar", "sí", "si", "yes", "confirm"]:
                deleted_count = self.quote_repository.clear_all_quotes()
                
                if deleted_count > 0:
                    success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                    await update.message.reply_text(
                        f"{success_message}\n\n*{deleted_count} frases* han sido eliminadas del archivo de la familia.",
                        parse_mode="Markdown"
                    )
                else:
                    error_message = self.theme_engine.generate_message(MessageType.ERROR)
                    await update.message.reply_text(error_message, parse_mode="Markdown")
            else:
                # Ask for confirmation
                confirmation_message = self.theme_engine.generate_message(
                    MessageType.CONFIRMATION,
                    name="capo"
                )
                
                await update.message.reply_text(
                    f"{confirmation_message}\n\n¿Estás seguro de que quieres eliminar *todas las {len(quotes)} frases* del archivo de la familia?\n\nEscribe `/clearquotes confirmar` para proceder.",
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Error clearing quotes: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_addhustle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /addhustle command - add a single quote to the database
        """
        if not context.args:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "No especificaste la frase a agregar",
                "Usa /addhustle [frase] para agregar una nueva frase motivacional"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        # Join all arguments to form the complete quote
        quote_text = " ".join(context.args).strip()
        
        if len(quote_text) < 10:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "La frase es demasiado corta",
                "Agrega una frase más inspiradora para la familia"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        if len(quote_text) > 500:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "La frase es demasiado larga",
                "Mantén la frase bajo 500 caracteres para mejor impacto"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        try:
            quote_id = self.quote_repository.add_quote(quote_text)
            
            if quote_id:
                success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                
                # Show preview of added quote
                quote_preview = quote_text[:100] + "..." if len(quote_text) > 100 else quote_text
                
                await update.message.reply_text(
                    f"{success_message}\n\n*Nueva frase agregada al libro de la familia:*\n\n\"{quote_preview}\"",
                    parse_mode="Markdown"
                )
            else:
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(
                    f"{error_message}\n\nNo se pudo agregar la frase al archivo.",
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Error adding quote: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_setquoteinterval(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /setquoteinterval command - configure quote frequency
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return
        
        # Check if user is admin in group chat
        if chat.type != "private":
            try:
                chat_member = await context.bot.get_chat_member(chat.id, user.id)
                if chat_member.status not in ["creator", "administrator"]:
                    warning_message = self.theme_engine.generate_message(
                        MessageType.WARNING,
                        name=user.first_name
                    )
                    await update.message.reply_text(
                        f"{warning_message}\n\nSolo los administradores pueden configurar el intervalo de frases.",
                        parse_mode="Markdown"
                    )
                    return
            except Exception as e:
                logger.error(f"Error checking admin status: {e}")
                return
        
        if not context.args:
            # Show current interval
            try:
                current_interval = self.config_repository.get_config(
                    chat.id, 
                    "quote_interval", 
                    "50"  # Default interval
                )
                
                if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                    info_message = f"📊 *CONFIGURACIÓN ACTUAL*\n\nIntervalo de frases: cada *{current_interval}* mensajes"
                else:
                    info_message = f"📊 *¿CUÁNDO MOTIVAMOS A LA FAMILIA?*\n\nActualmente enviamos frases cada *{current_interval}* mensajes"
                
                await update.message.reply_text(
                    f"{info_message}\n\nPara cambiar el intervalo, usa: `/setquoteinterval [número]`\n\n_Ejemplo: /setquoteinterval 25_",
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                logger.error(f"Error getting quote interval: {e}")
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(error_message, parse_mode="Markdown")
            return
        
        try:
            interval = int(context.args[0])
            
            if interval < 5:
                error_msg = self.theme_engine.format_error_with_suggestion(
                    "El intervalo es demasiado pequeño",
                    "Usa un número mayor a 5 para no saturar a la familia"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            if interval > 1000:
                error_msg = self.theme_engine.format_error_with_suggestion(
                    "El intervalo es demasiado grande",
                    "Usa un número menor a 1000 para mantener activa la motivación"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            # Save the new interval
            self.config_repository.set_config(chat.id, "quote_interval", str(interval))
            
            # Reset message counter for this chat
            self.config_repository.set_config(chat.id, "message_count", "0")
            
            success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
            
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                config_message = f"Intervalo configurado: cada *{interval}* mensajes se enviará una frase motivacional."
            else:
                config_message = f"¡Perfecto! Ahora motivaremos a la familia cada *{interval}* mensajes. ¡Que empiece la inspiración!"
            
            await update.message.reply_text(
                f"{success_message}\n\n{config_message}",
                parse_mode="Markdown"
            )
            
        except ValueError:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "El intervalo debe ser un número válido",
                "Usa /setquoteinterval [número] con un número entero"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error setting quote interval: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_setstyle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /setstyle command - adjust bot tone (serious/humorous)
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return
        
        # Load current chat-specific style configuration
        self._load_chat_style(chat.id)
        
        # Check if user is admin in group chat
        if chat.type != "private":
            try:
                chat_member = await context.bot.get_chat_member(chat.id, user.id)
                if chat_member.status not in ["creator", "administrator"]:
                    warning_message = self.theme_engine.generate_message(
                        MessageType.WARNING,
                        name=user.first_name
                    )
                    await update.message.reply_text(
                        f"{warning_message}\n\nSolo los administradores pueden cambiar el estilo del bot.",
                        parse_mode="Markdown"
                    )
                    return
            except Exception as e:
                logger.error(f"Error checking admin status: {e}")
                return
        
        if not context.args:
            # Show current style
            try:
                current_style = self.config_repository.get_config(
                    chat.id, 
                    "bot_style", 
                    "serio"  # Default style
                )
                
                current_tone = self.theme_engine.get_tone()
                tone_display = "Serio" if current_tone == ToneStyle.SERIOUS else "Humorístico"
                
                if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                    info_message = f"🎭 *ESTILO ACTUAL DEL BOT*\n\nTono configurado: *{tone_display}*"
                else:
                    info_message = f"🎭 *¿CÓMO HABLA LA FAMILIA?*\n\nActualmente uso el tono: *{tone_display}*"
                
                await update.message.reply_text(
                    f"{info_message}\n\nPara cambiar el estilo, usa: `/setstyle [serio/humorístico]`\n\n_Ejemplo: /setstyle humorístico_",
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                logger.error(f"Error getting bot style: {e}")
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(error_message, parse_mode="Markdown")
            return
        
        try:
            style_arg = context.args[0].lower().strip()
            
            # Validate style argument
            valid_styles = {
                "serio": ToneStyle.SERIOUS,
                "serious": ToneStyle.SERIOUS,
                "humorístico": ToneStyle.HUMOROUS,
                "humoristico": ToneStyle.HUMOROUS,
                "humorous": ToneStyle.HUMOROUS,
                "divertido": ToneStyle.HUMOROUS,
                "gracioso": ToneStyle.HUMOROUS
            }
            
            if style_arg not in valid_styles:
                error_msg = self.theme_engine.format_error_with_suggestion(
                    f"Estilo no reconocido: '{style_arg}'",
                    "Usa 'serio' o 'humorístico' para configurar el tono del bot"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            new_tone = valid_styles[style_arg]
            
            # Update theme engine tone
            self.theme_engine.set_tone(new_tone)
            
            # Save the new style to database
            style_value = "serio" if new_tone == ToneStyle.SERIOUS else "humorístico"
            self.config_repository.set_config(chat.id, "bot_style", style_value)
            
            # Generate success message with new tone
            success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
            
            tone_display = "Serio" if new_tone == ToneStyle.SERIOUS else "Humorístico"
            
            if new_tone == ToneStyle.SERIOUS:
                style_message = f"Estilo configurado a: *{tone_display}*\n\nLa familia ahora hablará con más seriedad y respeto."
            else:
                style_message = f"¡Estilo configurado a: *{tone_display}*!\n\n¡Ahora la familia será más divertida y relajada!"
            
            await update.message.reply_text(
                f"{success_message}\n\n{style_message}",
                parse_mode="Markdown"
            )
            
        except IndexError:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "No especificaste el estilo",
                "Usa /setstyle [serio/humorístico] para cambiar el tono del bot"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error setting bot style: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")

    async def handle_uploadquotes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /uploadquotes command - process uploaded quote files
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return
        
        # Check if user is admin in group chat
        if chat.type != "private":
            try:
                chat_member = await context.bot.get_chat_member(chat.id, user.id)
                if chat_member.status not in ["creator", "administrator"]:
                    warning_message = self.theme_engine.generate_message(
                        MessageType.WARNING,
                        name=user.first_name
                    )
                    await update.message.reply_text(
                        f"{warning_message}\n\nSolo los administradores pueden subir archivos de frases.",
                        parse_mode="Markdown"
                    )
                    return
            except Exception as e:
                logger.error(f"Error checking admin status: {e}")
                return
        
        # Check if message has a document attachment
        if not update.message.document:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "No se encontró ningún archivo adjunto",
                "Adjunta un archivo .txt, .csv o .json con las frases y usa /uploadquotes"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        document = update.message.document
        
        # Validate file size (max 10MB)
        max_file_size = 10 * 1024 * 1024  # 10MB in bytes
        if document.file_size > max_file_size:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "El archivo es demasiado grande",
                "El archivo debe ser menor a 10MB. Divide el archivo en partes más pequeñas."
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        # Validate file extension
        file_name = document.file_name or "unknown"
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ""
        
        if file_ext not in ['txt', 'csv', 'json']:
            error_msg = "Capo, ese archivo no es de la familia. Solo acepto .txt, .csv o .json."
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        try:
            # Send processing message
            processing_message = await update.message.reply_text(
                "🔄 *Procesando archivo...*\n\nLa familia está revisando las frases, capo.",
                parse_mode="Markdown"
            )
            
            # Download the file
            file = await context.bot.get_file(document.file_id)
            file_path = f"temp_{document.file_id}.{file_ext}"
            
            await file.download_to_drive(file_path)
            
            # Process the file
            quotes, error_message = self.file_processor.process_file(file_path)
            
            # Clean up temporary file
            import os
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                logger.warning(f"Could not remove temporary file {file_path}: {cleanup_error}")
            
            if error_message:
                # Edit the processing message with error
                await processing_message.edit_text(
                    f"❌ *Error procesando archivo*\n\n{error_message}",
                    parse_mode="Markdown"
                )
                return
            
            if not quotes:
                # Edit the processing message with empty file warning
                warning_msg = "⚠️ *Archivo vacío*\n\nEl archivo no contiene frases válidas, capo. Revisa el formato y contenido."
                await processing_message.edit_text(warning_msg, parse_mode="Markdown")
                return
            
            # Add quotes to database
            added_count = 0
            failed_count = 0
            
            for quote in quotes:
                try:
                    quote_id = self.quote_repository.add_quote(quote)
                    if quote_id:
                        added_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error adding quote '{quote[:50]}...': {e}")
                    failed_count += 1
            
            # Edit the processing message with results
            if added_count > 0:
                success_message = "✅ *¡Capo, las frases han sido añadidas al libro de la familia!*"
                
                if failed_count > 0:
                    result_text = f"{success_message}\n\n📊 *Resultados:*\n• Frases agregadas: *{added_count}*\n• Frases fallidas: *{failed_count}*"
                else:
                    result_text = f"{success_message}\n\n📊 *Total agregado:* *{added_count}* frases nuevas"
                
                # Add file info
                result_text += f"\n\n📄 *Archivo procesado:* {file_name}"
                
                # Add iconic phrase
                if self.theme_engine.get_tone() == ToneStyle.HUMOROUS:
                    result_text += f"\n\n_{self.theme_engine.get_iconic_phrase()}_"
                
                await processing_message.edit_text(result_text, parse_mode="Markdown")
            else:
                error_msg = "❌ *Error*\n\nNo se pudo agregar ninguna frase al archivo de la familia. Revisa el formato del archivo."
                await processing_message.edit_text(error_msg, parse_mode="Markdown")
                
        except Exception as e:
            logger.error(f"Error processing file upload: {e}")
            
            # Try to edit the processing message, or send a new one if that fails
            try:
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await processing_message.edit_text(
                    f"{error_message}\n\nHubo un problema procesando el archivo. Inténtalo de nuevo, capo.",
                    parse_mode="Markdown"
                )
            except:
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(
                    f"{error_message}\n\nHubo un problema procesando el archivo. Inténtalo de nuevo, capo.",
                    parse_mode="Markdown"
                )
    
    async def handle_setinactive(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /setinactive command - configure inactivity threshold
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return
        
        # Check if user is admin in group chat
        if chat.type != "private":
            try:
                chat_member = await context.bot.get_chat_member(chat.id, user.id)
                if chat_member.status not in ["creator", "administrator"]:
                    warning_message = self.theme_engine.generate_message(
                        MessageType.WARNING,
                        name=user.first_name
                    )
                    await update.message.reply_text(
                        f"{warning_message}\n\nSolo los administradores pueden configurar el umbral de inactividad.",
                        parse_mode="Markdown"
                    )
                    return
            except Exception as e:
                logger.error(f"Error checking admin status: {e}")
                return
        
        if not context.args:
            # Show current inactivity threshold
            try:
                current_threshold = self.config_repository.get_config(
                    chat.id, 
                    "inactive_days", 
                    "7"  # Default threshold
                )
                
                inactive_enabled = self.config_repository.get_config(
                    chat.id,
                    "inactive_enabled",
                    "true"
                ).lower() == "true"
                
                status = "activado" if inactive_enabled else "desactivado"
                
                if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                    info_message = f"📊 *CONFIGURACIÓN ACTUAL*\n\nUmbral de inactividad: *{current_threshold}* días\nEstado: *{status}*"
                else:
                    info_message = f"📊 *¿CUÁNDO DORMIRÁN CON LOS PECES?*\n\nActualmente, los miembros inactivos por *{current_threshold}* días recibirán una advertencia\nEstado: *{status}*"
                
                await update.message.reply_text(
                    f"{info_message}\n\nPara cambiar el umbral, usa: `/setinactive [días]`\n\n_Ejemplo: /setinactive 14_",
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                logger.error(f"Error getting inactivity threshold: {e}")
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(error_message, parse_mode="Markdown")
            return
        
        try:
            days = int(context.args[0])
            
            if days < 1:
                error_msg = self.theme_engine.format_error_with_suggestion(
                    "El umbral es demasiado pequeño",
                    "Usa un número mayor a 1 día para dar tiempo a los miembros"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            if days > 90:
                error_msg = self.theme_engine.format_error_with_suggestion(
                    "El umbral es demasiado grande",
                    "Usa un número menor a 90 días para mantener el grupo activo"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            # Save the new threshold
            self.config_repository.set_config(chat.id, "inactive_days", str(days))
            
            # Enable inactive user detection if it was disabled
            self.config_repository.set_config(chat.id, "inactive_enabled", "true")
            
            success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
            
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                config_message = f"Umbral configurado: los miembros inactivos por *{days}* días recibirán una advertencia."
            else:
                config_message = f"¡Perfecto! Ahora los miembros que estén *{days}* días sin actividad recibirán una advertencia. ¡La familia no tolera holgazanes!"
            
            await update.message.reply_text(
                f"{success_message}\n\n{config_message}",
                parse_mode="Markdown"
            )
            
        except ValueError:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "El umbral debe ser un número válido",
                "Usa /setinactive [días] con un número entero"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error setting inactivity threshold: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_disableinactive(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /disableinactive command - disable automatic inactive user removal
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return
        
        # Check if user is admin in group chat
        if chat.type != "private":
            try:
                chat_member = await context.bot.get_chat_member(chat.id, user.id)
                if chat_member.status not in ["creator", "administrator"]:
                    warning_message = self.theme_engine.generate_message(
                        MessageType.WARNING,
                        name=user.first_name
                    )
                    await update.message.reply_text(
                        f"{warning_message}\n\nSolo los administradores pueden desactivar la gestión de inactividad.",
                        parse_mode="Markdown"
                    )
                    return
            except Exception as e:
                logger.error(f"Error checking admin status: {e}")
                return
        
        try:
            # Check current status
            current_status = self.config_repository.get_config(
                chat.id,
                "inactive_enabled",
                "true"
            ).lower()
            
            if current_status == "false":
                # Already disabled
                info_message = self.theme_engine.generate_message(
                    MessageType.INFO,
                    name=user.first_name
                )
                
                await update.message.reply_text(
                    f"{info_message}\n\nLa gestión de inactividad ya está desactivada. Usa `/setinactive [días]` para activarla nuevamente.",
                    parse_mode="Markdown"
                )
                return
            
            # Disable inactive user management
            self.config_repository.set_config(chat.id, "inactive_enabled", "false")
            
            success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
            
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                config_message = "La gestión automática de usuarios inactivos ha sido desactivada."
            else:
                config_message = "¡Entendido! La familia será más tolerante con los miembros inactivos. Todos tienen una segunda oportunidad... por ahora."
            
            await update.message.reply_text(
                f"{success_message}\n\n{config_message}",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error disabling inactive user management: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
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
    
    async def handle_remind(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /remind command - schedule reminders with date, time, and message
        
        Formats:
        - /remind [date] [time] [message] - One-time reminder
        - /remind weekly [day] [time] [message] - Weekly recurring reminder
        
        Examples:
        - /remind tomorrow 15:00 Call the client
        - /remind 25/07 14:30 Team meeting
        - /remind weekly monday 10:00 Weekly report submission
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return
        
        if not context.args or len(context.args) < 3:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "Formato incorrecto para el recordatorio",
                "Usa /remind [fecha] [hora] [mensaje] o /remind weekly [día] [hora] [mensaje]"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        # Check if this is a recurring reminder
        is_recurring = False
        recurrence_pattern = None
        
        if context.args[0].lower() == "weekly":
            is_recurring = True
            recurrence_pattern = "weekly"
            
            if len(context.args) < 4:
                error_msg = self.theme_engine.format_error_with_suggestion(
                    "Formato incorrecto para recordatorio semanal",
                    "Usa /remind weekly [día] [hora] [mensaje]"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            # Parse day of week
            day_of_week = context.args[1].lower()
            valid_days = {
                "lunes": 0, "monday": 0, "l": 0, "mon": 0,
                "martes": 1, "tuesday": 1, "m": 1, "tue": 1,
                "miércoles": 2, "miercoles": 2, "wednesday": 2, "x": 2, "wed": 2,
                "jueves": 3, "thursday": 3, "j": 3, "thu": 3,
                "viernes": 4, "friday": 4, "v": 4, "fri": 4,
                "sábado": 5, "sabado": 5, "saturday": 5, "s": 5, "sat": 5,
                "domingo": 6, "sunday": 6, "d": 6, "sun": 6
            }
            
            if day_of_week not in valid_days:
                error_msg = self.theme_engine.format_error_with_suggestion(
                    f"Día de la semana no válido: {day_of_week}",
                    "Usa un día como 'lunes', 'martes', etc."
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            # Calculate next occurrence of this day
            today = datetime.now()
            days_ahead = valid_days[day_of_week] - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            target_date = today + timedelta(days=days_ahead)
            date_str = target_date.strftime("%d/%m/%Y")
            time_str = context.args[2]
            message_text = " ".join(context.args[3:])
            
        else:
            # One-time reminder
            date_str = context.args[0]
            time_str = context.args[1]
            message_text = " ".join(context.args[2:])
        
        # Parse date
        try:
            remind_time = self._parse_reminder_datetime(date_str, time_str)
            
            # Validate reminder time is in the future
            if remind_time <= datetime.now():
                error_msg = self.theme_engine.format_error_with_suggestion(
                    "El recordatorio debe ser para un momento futuro",
                    "Especifica una fecha y hora en el futuro"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            # Create the reminder
            reminder_id = self.reminder_repository.create_reminder(
                chat_id=chat.id,
                user_id=user.id,
                message=message_text,
                remind_time=remind_time,
                is_recurring=is_recurring,
                recurrence_pattern=recurrence_pattern
            )
            
            if reminder_id:
                success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                
                # Format reminder confirmation
                formatted_date = remind_time.strftime("%d/%m/%Y")
                formatted_time = remind_time.strftime("%H:%M")
                
                if is_recurring:
                    day_names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
                    day_name = day_names[remind_time.weekday()]
                    confirmation = f"Recordatorio semanal programado para cada *{day_name}* a las *{formatted_time}*"
                else:
                    confirmation = f"Recordatorio programado para el *{formatted_date}* a las *{formatted_time}*"
                
                await update.message.reply_text(
                    f"{success_message}\n\n{confirmation}\n\nMensaje: \"{message_text}\"\n\nLa familia te lo recordará a tiempo, capo.",
                    parse_mode="Markdown"
                )
            else:
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(
                    f"{error_message}\n\nNo se pudo crear el recordatorio. Inténtalo de nuevo.",
                    parse_mode="Markdown"
                )
                
        except ValueError as e:
            error_msg = self.theme_engine.format_error_with_suggestion(
                str(e),
                "Usa formatos como '25/07' o 'tomorrow' para la fecha y '15:30' para la hora"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /reminders command - list all active reminders
        """
        chat = update.effective_chat
        
        if not chat:
            return
        
        try:
            # Get all active reminders for this chat
            reminders = self.reminder_repository.get_active_reminders(chat.id)
            
            if not reminders:
                warning_message = self.theme_engine.generate_message(
                    MessageType.WARNING,
                    name="capo"
                )
                await update.message.reply_text(
                    f"{warning_message}\n\nNo hay recordatorios activos para este chat.",
                    parse_mode="Markdown"
                )
                return
            
            # Format reminders list with mafia theming
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                header = "📅 *AGENDA DE LA FAMILIA* 📅\n\nRecordatorios pendientes:"
            else:
                header = "📅 *¡LA MEMORIA DE DON CORLEONE!* 📅\n\nPorque hasta los mafiosos necesitan recordatorios:"
            
            reminder_lines = []
            for i, reminder in enumerate(reminders, 1):
                # Format date and time
                formatted_date = reminder.remind_time.strftime("%d/%m/%Y")
                formatted_time = reminder.remind_time.strftime("%H:%M")
                
                if reminder.is_recurring:
                    day_names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
                    day_name = day_names[reminder.remind_time.weekday()]
                    time_str = f"Cada {day_name} a las {formatted_time}"
                else:
                    time_str = f"{formatted_date} a las {formatted_time}"
                
                reminder_lines.append(f"{i}. *{time_str}*: {reminder.message}")
            
            reminders_text = "\n\n".join(reminder_lines)
            footer = f"\n\n_Total: {len(reminders)} recordatorios pendientes_"
            
            await update.message.reply_text(
                f"{header}\n\n{reminders_text}{footer}",
                parse_mode="Markdown"
            )
                
        except Exception as e:
            logger.error(f"Error listing reminders: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    def _parse_reminder_datetime(self, date_str: str, time_str: str) -> datetime:
        """
        Parse date and time strings into a datetime object
        
        Args:
            date_str: Date string (e.g., '25/07', 'tomorrow', 'today')
            time_str: Time string (e.g., '15:30')
            
        Returns:
            Parsed datetime object
            
        Raises:
            ValueError: If date or time format is invalid
        """
        # Parse time first
        time_match = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
        if not time_match:
            raise ValueError(f"Formato de hora inválido: {time_str}. Usa formato HH:MM (24h)")
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        
        if hour < 0 or hour > 23:
            raise ValueError(f"Hora inválida: {hour}. Debe estar entre 0 y 23")
        
        if minute < 0 or minute > 59:
            raise ValueError(f"Minutos inválidos: {minute}. Deben estar entre 0 y 59")
        
        # Parse date
        today = datetime.now()
        target_date = None
        
        # Check for special date keywords
        if date_str.lower() == 'today' or date_str.lower() == 'hoy':
            target_date = today
        elif date_str.lower() == 'tomorrow' or date_str.lower() == 'mañana' or date_str.lower() == 'manana':
            target_date = today + timedelta(days=1)
        else:
            # Try to parse as DD/MM or DD/MM/YY or DD/MM/YYYY
            date_formats = [
                (r'^(\d{1,2})/(\d{1,2})$', '%d/%m/%Y'),  # DD/MM format
                (r'^(\d{1,2})/(\d{1,2})/(\d{2})$', '%d/%m/%y'),  # DD/MM/YY format
                (r'^(\d{1,2})/(\d{1,2})/(\d{4})$', '%d/%m/%Y')  # DD/MM/YYYY format
            ]
            
            parsed = False
            for pattern, fmt in date_formats:
                if re.match(pattern, date_str):
                    try:
                        if fmt == '%d/%m/%Y' and len(date_str.split('/')) == 2:
                            # For DD/MM format, add current year
                            parts = date_str.split('/')
                            date_str = f"{parts[0]}/{parts[1]}/{today.year}"
                        
                        parsed_date = datetime.strptime(date_str, fmt)
                        # Set year to current year if not specified
                        if fmt == '%d/%m/%Y':
                            target_date = parsed_date.replace(year=today.year)
                        else:
                            target_date = parsed_date
                        
                        parsed = True
                        break
                    except ValueError:
                        continue
            
            if not parsed:
                raise ValueError(f"Formato de fecha inválido: {date_str}. Usa DD/MM o 'tomorrow'")
        
        # If the date is in the past (e.g., specifying a day that already passed this year)
        # then assume the next year
        result_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if result_datetime < today and date_str.lower() not in ['today', 'hoy']:
            result_datetime = result_datetime.replace(year=today.year + 1)
        
        return result_datetime
    
    async def handle_tag(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /tag command - tag messages with specified labels
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return
        
        if not context.args:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "No especificaste la etiqueta",
                "Responde a un mensaje con /tag [etiqueta] para etiquetarlo"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        # Check if this is a reply to another message
        if not update.message.reply_to_message:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "Debes responder a un mensaje para etiquetarlo",
                "Responde al mensaje que quieres etiquetar y usa /tag [etiqueta]"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        tag = " ".join(context.args).strip().lower()
        
        if len(tag) < 2:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "La etiqueta es demasiado corta",
                "Usa una etiqueta de al menos 2 caracteres"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        if len(tag) > 50:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "La etiqueta es demasiado larga",
                "Mantén la etiqueta bajo 50 caracteres"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        try:
            replied_message = update.message.reply_to_message
            message_content = replied_message.text or replied_message.caption or "[Mensaje multimedia]"
            
            # Save the tagged message
            saved_id = self.message_repository.save_message(
                chat_id=chat.id,
                message_id=replied_message.message_id,
                content=message_content,
                saved_by=user.id,
                tag=tag
            )
            
            if saved_id:
                success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                
                # Preview of tagged content
                content_preview = message_content[:100] + "..." if len(message_content) > 100 else message_content
                
                if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                    tag_message = f"Mensaje etiquetado como '*{tag}*' en los archivos de la familia."
                else:
                    tag_message = f"¡Perfecto! Mensaje guardado con la etiqueta '*{tag}*' en nuestros negocios etiquetados."
                
                await update.message.reply_text(
                    f"{success_message}\n\n{tag_message}\n\n*Contenido:* {content_preview}",
                    parse_mode="Markdown"
                )
            else:
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(
                    f"{error_message}\n\nNo se pudo etiquetar el mensaje.",
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Error tagging message: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_searchtag(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /searchtag command - retrieve tagged messages
        """
        chat = update.effective_chat
        
        if not chat:
            return
        
        if not context.args:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "No especificaste qué etiqueta buscar",
                "Usa /searchtag [etiqueta] para buscar mensajes etiquetados"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        tag = " ".join(context.args).strip().lower()
        
        try:
            tagged_messages = self.message_repository.get_messages_by_tag(chat.id, tag)
            
            if not tagged_messages:
                if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                    no_messages = f"No se encontraron mensajes con la etiqueta '*{tag}*' en los archivos de la familia."
                else:
                    no_messages = f"¡Ups! No hay negocios etiquetados como '*{tag}*' en nuestros archivos, capo."
                
                warning_message = self.theme_engine.generate_message(
                    MessageType.WARNING,
                    name="capo"
                )
                await update.message.reply_text(
                    f"{warning_message}\n\n{no_messages}",
                    parse_mode="Markdown"
                )
                return
            
            # Format tagged messages with mafia theming
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                header = f"🏷️ *MENSAJES ETIQUETADOS: {tag.upper()}* 🏷️\n\nArchivos de la familia con esta etiqueta:"
            else:
                header = f"🏷️ *NEGOCIOS ETIQUETADOS: {tag.upper()}* 🏷️\n\n¡Aquí están todos los mensajes que guardamos con esta etiqueta!"
            
            message_lines = []
            for i, msg in enumerate(tagged_messages, 1):
                # Format date
                date_str = msg.created_at.strftime("%d/%m/%Y %H:%M") if msg.created_at else "Fecha desconocida"
                
                # Truncate long messages for display
                content_preview = msg.content
                if len(content_preview) > 150:
                    content_preview = content_preview[:147] + "..."
                
                message_lines.append(f"{i}. *{date_str}*\n   {content_preview}")
            
            # Split into chunks if too many messages
            max_messages_per_chunk = 10
            if len(message_lines) <= max_messages_per_chunk:
                messages_text = "\n\n".join(message_lines)
                footer = f"\n\n_Total: {len(tagged_messages)} mensajes con etiqueta '{tag}'_"
                
                await update.message.reply_text(
                    f"{header}\n\n{messages_text}{footer}",
                    parse_mode="Markdown"
                )
            else:
                # Send in chunks
                for i in range(0, len(message_lines), max_messages_per_chunk):
                    chunk = message_lines[i:i + max_messages_per_chunk]
                    chunk_text = "\n\n".join(chunk)
                    
                    if i == 0:
                        message = f"{header}\n\n{chunk_text}"
                    else:
                        message = f"🏷️ *Continuación: {tag.upper()}* 🏷️\n\n{chunk_text}"
                    
                    if i + max_messages_per_chunk >= len(message_lines):
                        message += f"\n\n_Total: {len(tagged_messages)} mensajes con etiqueta '{tag}'_"
                    
                    await update.message.reply_text(message, parse_mode="Markdown")
                    
        except Exception as e:
            logger.error(f"Error searching tagged messages: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_save(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /save command - store important messages
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return
        
        # Check if this is a reply to another message
        if update.message.reply_to_message:
            # Save the replied message
            replied_message = update.message.reply_to_message
            message_content = replied_message.text or replied_message.caption or "[Mensaje multimedia]"
            
            try:
                saved_id = self.message_repository.save_message(
                    chat_id=chat.id,
                    message_id=replied_message.message_id,
                    content=message_content,
                    saved_by=user.id,
                    tag=None  # No tag for saved messages
                )
                
                if saved_id:
                    success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                    
                    # Preview of saved content
                    content_preview = message_content[:100] + "..." if len(message_content) > 100 else message_content
                    
                    if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                        save_message = "Mensaje guardado en los archivos importantes de la familia."
                    else:
                        save_message = "¡Perfecto! Mensaje guardado en nuestros negocios importantes que la familia necesita recordar."
                    
                    await update.message.reply_text(
                        f"{success_message}\n\n{save_message}\n\n*Contenido:* {content_preview}",
                        parse_mode="Markdown"
                    )
                else:
                    error_message = self.theme_engine.generate_message(MessageType.ERROR)
                    await update.message.reply_text(
                        f"{error_message}\n\nNo se pudo guardar el mensaje.",
                        parse_mode="Markdown"
                    )
                    
            except Exception as e:
                logger.error(f"Error saving message: {e}")
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(error_message, parse_mode="Markdown")
                
        elif context.args:
            # Save the provided text as a message
            message_text = " ".join(context.args).strip()
            
            if len(message_text) < 5:
                error_msg = self.theme_engine.format_error_with_suggestion(
                    "El mensaje es demasiado corto",
                    "Proporciona un mensaje más largo para guardar"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            if len(message_text) > 1000:
                error_msg = self.theme_engine.format_error_with_suggestion(
                    "El mensaje es demasiado largo",
                    "Mantén el mensaje bajo 1000 caracteres"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            try:
                saved_id = self.message_repository.save_message(
                    chat_id=chat.id,
                    message_id=update.message.message_id,
                    content=message_text,
                    saved_by=user.id,
                    tag=None
                )
                
                if saved_id:
                    success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                    
                    # Preview of saved content
                    content_preview = message_text[:100] + "..." if len(message_text) > 100 else message_text
                    
                    if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                        save_message = "Texto guardado en los archivos importantes de la familia."
                    else:
                        save_message = "¡Excelente! Texto guardado en nuestros negocios importantes."
                    
                    await update.message.reply_text(
                        f"{success_message}\n\n{save_message}\n\n*Contenido:* {content_preview}",
                        parse_mode="Markdown"
                    )
                else:
                    error_message = self.theme_engine.generate_message(MessageType.ERROR)
                    await update.message.reply_text(
                        f"{error_message}\n\nNo se pudo guardar el texto.",
                        parse_mode="Markdown"
                    )
                    
            except Exception as e:
                logger.error(f"Error saving text: {e}")
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(error_message, parse_mode="Markdown")
        else:
            # No reply message and no arguments
            error_msg = self.theme_engine.format_error_with_suggestion(
                "No especificaste qué guardar",
                "Responde a un mensaje con /save o usa /save [texto] para guardar texto"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
    
    async def handle_savedmessages(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /savedmessages command - list all saved messages
        """
        chat = update.effective_chat
        
        if not chat:
            return
        
        try:
            # Get all saved messages (those without tags)
            all_saved = self.message_repository.get_saved_messages(chat.id)
            saved_messages = [msg for msg in all_saved if not msg.tag]
            
            if not saved_messages:
                if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                    no_messages = "No hay mensajes guardados en los archivos importantes de la familia."
                else:
                    no_messages = "¡Ups! No hay negocios importantes guardados en nuestros archivos, capo."
                
                warning_message = self.theme_engine.generate_message(
                    MessageType.WARNING,
                    name="capo"
                )
                await update.message.reply_text(
                    f"{warning_message}\n\n{no_messages}",
                    parse_mode="Markdown"
                )
                return
            
            # Format saved messages with mafia theming
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                header = "💾 *MENSAJES IMPORTANTES DE LA FAMILIA* 💾\n\nArchivos que la familia necesita recordar:"
            else:
                header = "💾 *NEGOCIOS IMPORTANTES QUE LA FAMILIA NECESITA RECORDAR* 💾\n\n¡Aquí están todos los mensajes importantes!"
            
            message_lines = []
            for i, msg in enumerate(saved_messages, 1):
                # Format date
                date_str = msg.created_at.strftime("%d/%m/%Y %H:%M") if msg.created_at else "Fecha desconocida"
                
                # Truncate long messages for display
                content_preview = msg.content
                if len(content_preview) > 150:
                    content_preview = content_preview[:147] + "..."
                
                message_lines.append(f"{i}. *{date_str}*\n   {content_preview}")
            
            # Split into chunks if too many messages
            max_messages_per_chunk = 10
            if len(message_lines) <= max_messages_per_chunk:
                messages_text = "\n\n".join(message_lines)
                footer = f"\n\n_Total: {len(saved_messages)} mensajes importantes guardados_"
                
                await update.message.reply_text(
                    f"{header}\n\n{messages_text}{footer}",
                    parse_mode="Markdown"
                )
            else:
                # Send in chunks
                for i in range(0, len(message_lines), max_messages_per_chunk):
                    chunk = message_lines[i:i + max_messages_per_chunk]
                    chunk_text = "\n\n".join(chunk)
                    
                    if i == 0:
                        message = f"{header}\n\n{chunk_text}"
                    else:
                        message = f"💾 *Continuación: Mensajes Importantes* 💾\n\n{chunk_text}"
                    
                    if i + max_messages_per_chunk >= len(message_lines):
                        message += f"\n\n_Total: {len(saved_messages)} mensajes importantes guardados_"
                    
                    await update.message.reply_text(message, parse_mode="Markdown")
                    
        except Exception as e:
            logger.error(f"Error retrieving saved messages: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_addcommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /addcommand command - create custom bot commands
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return
        
        # Check if user is admin in group chat
        if chat.type != "private":
            try:
                chat_member = await context.bot.get_chat_member(chat.id, user.id)
                if chat_member.status not in ["creator", "administrator"]:
                    warning_message = self.theme_engine.generate_message(
                        MessageType.WARNING,
                        name=user.first_name
                    )
                    await update.message.reply_text(
                        f"{warning_message}\n\nSolo los administradores pueden crear comandos personalizados para la familia.",
                        parse_mode="Markdown"
                    )
                    return
            except Exception as e:
                logger.error(f"Error checking admin status: {e}")
                return
        
        if len(context.args) < 2:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "Faltan parámetros para crear el comando",
                "Usa /addcommand [nombre] [respuesta] para crear un comando personalizado"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        command_name = context.args[0].lower().strip()
        response_text = " ".join(context.args[1:]).strip()
        
        # Validate command name
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', command_name):
            error_msg = self.theme_engine.format_error_with_suggestion(
                "Nombre de comando inválido",
                "El nombre debe empezar con una letra y solo contener letras, números y guiones bajos"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        # Check if command name conflicts with existing bot commands
        reserved_commands = {
            "start", "help", "rules", "hustle", "motivate", "listquotes", 
            "deletequote", "clearquotes", "addhustle", "setquoteinterval",
            "tag", "searchtag", "save", "savedmessages", "remind", "reminders",
            "setinactive", "disableinactive", "addcommand", "customcommands",
            "deletecommand", "welcome", "setstyle", "filter"
        }
        
        if command_name in reserved_commands:
            error_msg = self.theme_engine.format_error_with_suggestion(
                f"El comando '{command_name}' está reservado por la familia",
                "Elige un nombre diferente para tu comando personalizado"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        # Validate response length
        if len(response_text) < 1:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "La respuesta del comando no puede estar vacía",
                "Proporciona una respuesta para el comando personalizado"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        if len(response_text) > 1000:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "La respuesta es demasiado larga",
                "Mantén la respuesta bajo 1000 caracteres"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        try:
            # Check if command already exists
            existing_command = self.custom_command_repository.get_custom_command(chat.id, command_name)
            
            if existing_command:
                # Update existing command
                self.custom_command_repository.delete_custom_command(chat.id, command_name)
                command_id = self.custom_command_repository.add_custom_command(
                    chat.id, command_name, response_text, user.id
                )
                
                success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                await update.message.reply_text(
                    f"{success_message}\n\n*Comando actualizado:* /{command_name}\n\n*Nueva respuesta:* {response_text[:100]}{'...' if len(response_text) > 100 else ''}",
                    parse_mode="Markdown"
                )
            else:
                # Create new command
                command_id = self.custom_command_repository.add_custom_command(
                    chat.id, command_name, response_text, user.id
                )
                
                success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                await update.message.reply_text(
                    f"{success_message}\n\n*Nuevo comando creado:* /{command_name}\n\n*Respuesta:* {response_text[:100]}{'...' if len(response_text) > 100 else ''}",
                    parse_mode="Markdown"
                )
            
            # Register the command dynamically
            await self._register_custom_command(context.application, chat.id, command_name)
            
        except Exception as e:
            logger.error(f"Error creating custom command: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(
                f"{error_message}\n\nNo se pudo crear el comando personalizado.",
                parse_mode="Markdown"
            )
    
    async def handle_customcommands(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /customcommands command - list all custom commands
        """
        chat = update.effective_chat
        
        if not chat:
            return
        
        try:
            custom_commands = self.custom_command_repository.get_all_custom_commands(chat.id)
            
            if not custom_commands:
                if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                    no_commands_message = "📋 *COMANDOS PERSONALIZADOS*\n\nNo hay comandos personalizados configurados para esta familia."
                else:
                    no_commands_message = "📋 *ARSENAL DE COMANDOS PERSONALIZADOS*\n\n¡Esta familia aún no tiene comandos personalizados! ¿Qué esperan?"
                
                await update.message.reply_text(
                    f"{no_commands_message}\n\nUsa `/addcommand [nombre] [respuesta]` para crear uno.",
                    parse_mode="Markdown"
                )
                return
            
            # Format commands list
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                header = "📋 *COMANDOS PERSONALIZADOS DE LA FAMILIA*\n\nComandos disponibles:"
            else:
                header = "📋 *ARSENAL DE COMANDOS PERSONALIZADOS*\n\n¡Aquí están las herramientas especiales de la familia!"
            
            command_lines = []
            for cmd in custom_commands:
                # Truncate long responses for display
                response_preview = cmd.response
                if len(response_preview) > 50:
                    response_preview = response_preview[:47] + "..."
                
                command_lines.append(f"/{cmd.command_name} - {response_preview}")
            
            # Split into chunks if too many commands
            max_commands_per_message = 15
            if len(command_lines) <= max_commands_per_message:
                commands_text = "\n\n".join(command_lines)
                footer = f"\n\n_Total: {len(custom_commands)} comandos personalizados_"
                
                await update.message.reply_text(
                    f"{header}\n\n{commands_text}{footer}",
                    parse_mode="Markdown"
                )
            else:
                # Send in chunks
                for i in range(0, len(command_lines), max_commands_per_message):
                    chunk = command_lines[i:i + max_commands_per_message]
                    chunk_text = "\n\n".join(chunk)
                    
                    if i == 0:
                        message = f"{header}\n\n{chunk_text}"
                    else:
                        message = f"📋 *Continuación...* 📋\n\n{chunk_text}"
                    
                    if i + max_commands_per_message >= len(command_lines):
                        message += f"\n\n_Total: {len(custom_commands)} comandos personalizados_"
                    
                    await update.message.reply_text(message, parse_mode="Markdown")
                    
        except Exception as e:
            logger.error(f"Error listing custom commands: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_deletecommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /deletecommand command - delete a custom command
        """
        chat = update.effective_chat
        user = update.effective_user
        
        if not chat or not user:
            return
        
        # Check if user is admin in group chat
        if chat.type != "private":
            try:
                chat_member = await context.bot.get_chat_member(chat.id, user.id)
                if chat_member.status not in ["creator", "administrator"]:
                    warning_message = self.theme_engine.generate_message(
                        MessageType.WARNING,
                        name=user.first_name
                    )
                    await update.message.reply_text(
                        f"{warning_message}\n\nSolo los administradores pueden eliminar comandos personalizados.",
                        parse_mode="Markdown"
                    )
                    return
            except Exception as e:
                logger.error(f"Error checking admin status: {e}")
                return
        
        if not context.args:
            error_msg = self.theme_engine.format_error_with_suggestion(
                "No especificaste qué comando eliminar",
                "Usa /deletecommand [nombre] para eliminar un comando personalizado"
            )
            await update.message.reply_text(error_msg, parse_mode="Markdown")
            return
        
        command_name = context.args[0].lower().strip()
        
        try:
            # Check if command exists
            existing_command = self.custom_command_repository.get_custom_command(chat.id, command_name)
            
            if not existing_command:
                error_msg = self.theme_engine.format_error_with_suggestion(
                    f"El comando '{command_name}' no existe",
                    "Usa /customcommands para ver los comandos disponibles"
                )
                await update.message.reply_text(error_msg, parse_mode="Markdown")
                return
            
            # Delete the command
            if self.custom_command_repository.delete_custom_command(chat.id, command_name):
                success_message = self.theme_engine.generate_message(MessageType.SUCCESS)
                
                # Show preview of deleted command
                response_preview = existing_command.response[:50] + "..." if len(existing_command.response) > 50 else existing_command.response
                
                await update.message.reply_text(
                    f"{success_message}\n\n*Comando eliminado:* /{command_name}\n*Respuesta:* {response_preview}",
                    parse_mode="Markdown"
                )
                
                # Unregister the command dynamically (if possible)
                await self._unregister_custom_command(context.application, command_name)
            else:
                error_message = self.theme_engine.generate_message(MessageType.ERROR)
                await update.message.reply_text(
                    f"{error_message}\n\nNo se pudo eliminar el comando.",
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Error deleting custom command: {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def handle_custom_command_execution(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command_name: str) -> None:
        """
        Handle execution of a custom command
        
        Args:
            update: Telegram update object
            context: Telegram context object
            command_name: Name of the custom command to execute
        """
        chat = update.effective_chat
        
        if not chat:
            return
        
        try:
            # Get the custom command from database
            custom_command = self.custom_command_repository.get_custom_command(chat.id, command_name)
            
            if not custom_command:
                # Command not found - this shouldn't happen if properly registered
                logger.warning(f"Custom command '{command_name}' not found in database for chat {chat.id}")
                return
            
            # Send the custom response with mafia theming
            response = custom_command.response
            
            # Add some mafia flair to the response if it doesn't already have it
            if not any(word in response.lower() for word in ["capo", "familia", "negocio", "don"]):
                if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                    response = f"🎯 {response}"
                else:
                    response = f"🎯 {response}\n\n_- Un mensaje de la familia_"
            
            await update.message.reply_text(
                response,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error executing custom command '{command_name}': {e}")
            error_message = self.theme_engine.generate_message(MessageType.ERROR)
            await update.message.reply_text(error_message, parse_mode="Markdown")
    
    async def _register_custom_command(self, application, chat_id: int, command_name: str) -> None:
        """
        Register a custom command dynamically with the application
        
        Args:
            application: Telegram bot application instance
            chat_id: Chat ID where the command is available
            command_name: Name of the command to register
        """
        try:
            # Create a handler function for this specific custom command
            async def custom_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                # Only respond in the chat where the command was created
                if update.effective_chat and update.effective_chat.id == chat_id:
                    await self.handle_custom_command_execution(update, context, command_name)
            
            # Add the handler to the application
            application.add_handler(TelegramCommandHandler(command_name, custom_handler))
            
            logger.info(f"Registered custom command '{command_name}' for chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error registering custom command '{command_name}': {e}")
    
    async def _unregister_custom_command(self, application, command_name: str) -> None:
        """
        Unregister a custom command from the application
        
        Args:
            application: Telegram bot application instance
            command_name: Name of the command to unregister
        """
        try:
            # Note: python-telegram-bot doesn't provide a direct way to remove handlers
            # This is a limitation of the library. The handler will remain registered
            # but the database lookup will fail, so it won't execute
            logger.info(f"Custom command '{command_name}' marked for removal (handler remains registered)")
            
        except Exception as e:
            logger.error(f"Error unregistering custom command '{command_name}': {e}")
    
    async def load_and_register_custom_commands(self, application) -> None:
        """
        Load all existing custom commands from database and register them
        
        Args:
            application: Telegram bot application instance
        """
        try:
            # Get all custom commands from all chats
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT DISTINCT chat_id, command_name FROM custom_commands")
                commands = cursor.fetchall()
            
            for row in commands:
                chat_id = row['chat_id']
                command_name = row['command_name']
                await self._register_custom_command(application, chat_id, command_name)
            
            logger.info(f"Loaded and registered {len(commands)} custom commands")
            
        except Exception as e:
            logger.error(f"Error loading custom commands: {e}")
    
    def register_command(self, command_name: str, handler_func: Callable):
        """
        Register a command handler function
        
        Args:
            command_name: Command name without slash
            handler_func: Handler function to call
        """
        self._command_registry[command_name] = handler_func
    
    def get_registered_commands(self) -> Dict[str, Callable]:
        """
        Get all registered commands
        
        Returns:
            Dictionary of command names to handler functions
        """
        return self._command_registry


def register_command_handlers(application):
    """
    Register all command handlers with the application
    
    Args:
        application: Telegram bot application instance
        
    Returns:
        CommandHandler instance for further configuration
    """
    # Create command handler with theme engine
    handler = CommandHandler(theme_engine)
    
    # Register basic commands
    application.add_handler(TelegramCommandHandler("start", handler.handle_start))
    application.add_handler(TelegramCommandHandler("rules", handler.handle_rules))
    application.add_handler(TelegramCommandHandler("help", handler.handle_help))
    application.add_handler(TelegramCommandHandler("hustle", handler.handle_hustle))
    application.add_handler(TelegramCommandHandler("motivate", handler.handle_hustle))  # Alias for hustle
    
    # Register quote management commands
    application.add_handler(TelegramCommandHandler("listquotes", handler.handle_listquotes))
    application.add_handler(TelegramCommandHandler("deletequote", handler.handle_deletequote))
    application.add_handler(TelegramCommandHandler("clearquotes", handler.handle_clearquotes))
    application.add_handler(TelegramCommandHandler("addhustle", handler.handle_addhustle))
    application.add_handler(TelegramCommandHandler("setquoteinterval", handler.handle_setquoteinterval))
    application.add_handler(TelegramCommandHandler("uploadquotes", handler.handle_uploadquotes))
    
    # Register message tagging commands
    application.add_handler(TelegramCommandHandler("tag", handler.handle_tag))
    application.add_handler(TelegramCommandHandler("searchtag", handler.handle_searchtag))
    
    # Register message saving commands
    application.add_handler(TelegramCommandHandler("save", handler.handle_save))
    application.add_handler(TelegramCommandHandler("savedmessages", handler.handle_savedmessages))
    
    # Register reminder commands
    application.add_handler(TelegramCommandHandler("remind", handler.handle_remind))
    application.add_handler(TelegramCommandHandler("reminders", handler.handle_reminders))
    
    # Register inactive user management commands
    application.add_handler(TelegramCommandHandler("setinactive", handler.handle_setinactive))
    application.add_handler(TelegramCommandHandler("disableinactive", handler.handle_disableinactive))
    
    # Register custom command management commands
    application.add_handler(TelegramCommandHandler("addcommand", handler.handle_addcommand))
    application.add_handler(TelegramCommandHandler("customcommands", handler.handle_customcommands))
    application.add_handler(TelegramCommandHandler("deletecommand", handler.handle_deletecommand))
    
    # Register bot configuration commands
    application.add_handler(TelegramCommandHandler("setstyle", handler.handle_setstyle))
    
    # Register commands in the handler's registry
    handler.register_command("start", handler.handle_start)
    handler.register_command("rules", handler.handle_rules)
    handler.register_command("help", handler.handle_help)
    handler.register_command("hustle", handler.handle_hustle)
    handler.register_command("motivate", handler.handle_hustle)
    handler.register_command("listquotes", handler.handle_listquotes)
    handler.register_command("deletequote", handler.handle_deletequote)
    handler.register_command("clearquotes", handler.handle_clearquotes)
    handler.register_command("addhustle", handler.handle_addhustle)
    handler.register_command("setquoteinterval", handler.handle_setquoteinterval)
    handler.register_command("uploadquotes", handler.handle_uploadquotes)
    handler.register_command("tag", handler.handle_tag)
    handler.register_command("searchtag", handler.handle_searchtag)
    handler.register_command("save", handler.handle_save)
    handler.register_command("savedmessages", handler.handle_savedmessages)
    handler.register_command("remind", handler.handle_remind)
    handler.register_command("reminders", handler.handle_reminders)
    handler.register_command("addcommand", handler.handle_addcommand)
    handler.register_command("customcommands", handler.handle_customcommands)
    handler.register_command("deletecommand", handler.handle_deletecommand)
    handler.register_command("setstyle", handler.handle_setstyle)
    
    logger.info("Command handlers registered successfully")
    
    # Return the handler instance for further configuration
    return handler