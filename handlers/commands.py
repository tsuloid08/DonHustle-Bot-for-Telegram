"""
Command handlers for @donhustle_bot
Implements all bot commands with mafia-themed responses
"""

import logging
import inspect
from typing import Dict, List, Optional, Callable, Any, Type
from abc import ABC, abstractmethod

from telegram import Update, Chat, User
from telegram.ext import ContextTypes, CommandHandler as TelegramCommandHandler
from telegram.constants import ParseMode

from utils.theme import ThemeEngine, MessageType, ToneStyle
from database.manager import get_database_manager
from database.repositories import QuoteRepository, ConfigRepository, UserActivityRepository, MessageRepository

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
        self._command_registry = {}
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command - introduction and help information
        """
        user = update.effective_user
        chat = update.effective_chat
        
        if not user or not chat:
            return
        
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
                    "setquoteinterval": "Configurar frecuencia de frases",
                    "setstyle": "Ajustar tono del bot (serio/humorístico)",
                    "listquotes": "Ver todas las frases motivacionales",
                    "addhustle": "Agregar una nueva frase motivacional",
                    "deletequote": "Eliminar una frase específica por número",
                    "clearquotes": "Eliminar todas las frases (requiere confirmación)"
                }
                commands.update(admin_commands)
        
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
    
    # Register message tagging commands
    application.add_handler(TelegramCommandHandler("tag", handler.handle_tag))
    application.add_handler(TelegramCommandHandler("searchtag", handler.handle_searchtag))
    
    # Register message saving commands
    application.add_handler(TelegramCommandHandler("save", handler.handle_save))
    application.add_handler(TelegramCommandHandler("savedmessages", handler.handle_savedmessages))
    
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
    handler.register_command("tag", handler.handle_tag)
    handler.register_command("searchtag", handler.handle_searchtag)
    handler.register_command("save", handler.handle_save)
    handler.register_command("savedmessages", handler.handle_savedmessages)
    
    logger.info("Command handlers registered successfully")