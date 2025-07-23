"""
Scheduler for background tasks in @donhustle_bot

Handles reminder scheduling and execution, as well as other periodic tasks.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from telegram.ext import Application, ContextTypes
from telegram.constants import ParseMode

from utils.theme import ThemeEngine, MessageType, ToneStyle
from database.repositories import ReminderRepository
from database.models import Reminder
from database.manager import get_database_manager

logger = logging.getLogger(__name__)


class BotScheduler:
    """
    Scheduler for managing and executing background tasks
    """
    
    def __init__(self, application: Application, theme_engine: ThemeEngine):
        """
        Initialize the bot scheduler
        
        Args:
            application: Telegram bot application
            theme_engine: ThemeEngine for mafia-themed messages
        """
        self.application = application
        self.theme_engine = theme_engine
        self.db_manager = get_database_manager()
        self.reminder_repository = ReminderRepository(self.db_manager)
        from database.repositories import UserActivityRepository, ConfigRepository
        self.user_activity_repository = UserActivityRepository(self.db_manager)
        self.config_repository = ConfigRepository(self.db_manager)
        self.is_running = False
        self._task = None
        self._processed_reminders = set()  # Track processed reminders to avoid duplicates
        self._warned_users = set()  # Track users who have been warned about inactivity
    
    async def start(self, check_interval: int = 60):
        """
        Start the reminder scheduler
        
        Args:
            check_interval: How often to check for due reminders (in seconds)
        """
        if self.is_running:
            logger.warning("Reminder scheduler is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run_scheduler(check_interval))
        logger.info(f"Reminder scheduler started with {check_interval}s interval")
    
    async def stop(self):
        """Stop the reminder scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info("Reminder scheduler stopped")
    
    async def _run_scheduler(self, check_interval: int):
        """
        Main scheduler loop that checks for due reminders and inactive users
        
        Args:
            check_interval: How often to check for scheduled tasks (in seconds)
        """
        while self.is_running:
            try:
                # Check reminders
                await self._check_reminders()
                
                # Check inactive users (less frequently)
                # Only check once per hour to avoid excessive database queries
                if datetime.now().minute == 0:
                    await self._check_inactive_users()
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
            
            # Wait for next check
            await asyncio.sleep(check_interval)
    
    async def _check_reminders(self):
        """Check for due reminders and send notifications"""
        current_time = datetime.now()
        
        # Get all due reminders
        due_reminders = self.reminder_repository.get_due_reminders(current_time)
        
        if not due_reminders:
            return
        
        logger.info(f"Found {len(due_reminders)} due reminders")
        
        for reminder in due_reminders:
            # Skip if we've already processed this reminder in this session
            # This prevents duplicate notifications if the scheduler runs multiple times
            # before the database is updated
            reminder_key = f"{reminder.id}_{reminder.remind_time.isoformat()}"
            if reminder_key in self._processed_reminders:
                continue
                
            try:
                # Send reminder notification
                await self._send_reminder(reminder)
                
                # Handle recurring reminders
                if reminder.is_recurring and reminder.recurrence_pattern == "weekly":
                    # Schedule next occurrence (7 days later)
                    next_time = reminder.remind_time + timedelta(days=7)
                    
                    # Create new reminder with updated time
                    new_reminder_id = self.reminder_repository.create_reminder(
                        chat_id=reminder.chat_id,
                        user_id=reminder.user_id,
                        message=reminder.message,
                        remind_time=next_time,
                        is_recurring=True,
                        recurrence_pattern="weekly"
                    )
                    
                    logger.info(f"Created recurring reminder {new_reminder_id} for next week")
                
                # Deactivate one-time reminders
                if not reminder.is_recurring:
                    self.reminder_repository.deactivate_reminder(reminder.id)
                    logger.info(f"Deactivated one-time reminder {reminder.id}")
                
                # Mark as processed to avoid duplicates
                self._processed_reminders.add(reminder_key)
                
                # Limit the size of the processed set to avoid memory issues
                if len(self._processed_reminders) > 1000:
                    self._processed_reminders = set(list(self._processed_reminders)[-500:])
                    
            except Exception as e:
                logger.error(f"Error processing reminder {reminder.id}: {e}")
    
    async def _send_reminder(self, reminder: Reminder):
        """
        Send a reminder notification
        
        Args:
            reminder: Reminder object to send
        """
        try:
            # Format reminder message with mafia theming
            reminder_message = self.theme_engine.generate_message(
                MessageType.REMINDER,
                message=reminder.message
            )
            
            # Add user mention if possible
            user_mention = f"<a href='tg://user?id={reminder.user_id}'>Capo</a>"
            
            # Create full message with mafia theming
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                full_message = f"⏰ *RECORDATORIO DE LA FAMILIA* ⏰\n\n{user_mention}, {reminder_message}"
            else:
                full_message = f"⏰ *¡DESPIERTA, SOLDADO!* ⏰\n\n{user_mention}, {reminder_message}"
            
            # Send the reminder
            await self.application.bot.send_message(
                chat_id=reminder.chat_id,
                text=full_message,
                parse_mode=ParseMode.HTML
            )
            
            logger.info(f"Sent reminder {reminder.id} to chat {reminder.chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending reminder {reminder.id}: {e}")
            raise
    
    async def _check_inactive_users(self):
        """Check for inactive users and send warnings or remove them"""
        try:
            # Get all chats with activity tracking
            chats_query = "SELECT DISTINCT chat_id FROM user_activity"
            chat_rows = self.db_manager.execute_query(chats_query)
            
            for row in chat_rows:
                chat_id = row['chat_id']
                
                # Check if inactive user management is enabled for this chat
                inactive_enabled = self.config_repository.get_config(
                    chat_id, 
                    "inactive_enabled", 
                    "true"
                ).lower() == "true"
                
                if not inactive_enabled:
                    continue
                
                # Get inactive threshold for this chat
                inactive_days = int(self.config_repository.get_config(
                    chat_id,
                    "inactive_days",
                    "7"  # Default: 7 days
                ))
                
                # Get warning period (default: 24 hours)
                warning_hours = int(self.config_repository.get_config(
                    chat_id,
                    "inactive_warning_hours",
                    "24"
                ))
                
                # Get inactive users
                inactive_users = self.user_activity_repository.get_inactive_users(chat_id, inactive_days)
                
                for user in inactive_users:
                    user_key = f"{user.user_id}_{chat_id}"
                    
                    # Calculate how long the user has been inactive
                    inactive_time = datetime.now() - user.last_activity
                    
                    # Check if user should be warned (inactive for threshold days)
                    if inactive_time.days >= inactive_days and user_key not in self._warned_users:
                        await self._warn_inactive_user(user.user_id, chat_id, inactive_days)
                        self._warned_users.add(user_key)
                        
                        # Store warning time in database
                        warning_time = datetime.now().isoformat()
                        self.config_repository.set_config(
                            chat_id,
                            f"inactive_warning_{user.user_id}",
                            warning_time
                        )
                    
                    # Check if user should be removed (warned and still inactive after warning period)
                    warning_time_str = self.config_repository.get_config(
                        chat_id,
                        f"inactive_warning_{user.user_id}",
                        None
                    )
                    
                    if warning_time_str:
                        warning_time = datetime.fromisoformat(warning_time_str)
                        time_since_warning = datetime.now() - warning_time
                        
                        # If warning period has passed and user is still inactive
                        if time_since_warning.total_seconds() / 3600 >= warning_hours:
                            await self._remove_inactive_user(user.user_id, chat_id)
                            
                            # Remove warning record and user from warned set
                            self.config_repository.delete_config(
                                chat_id,
                                f"inactive_warning_{user.user_id}"
                            )
                            if user_key in self._warned_users:
                                self._warned_users.remove(user_key)
                
        except Exception as e:
            logger.error(f"Error checking inactive users: {e}")
    
    async def _warn_inactive_user(self, user_id: int, chat_id: int, inactive_days: int):
        """
        Send a warning to an inactive user
        
        Args:
            user_id: User ID to warn
            chat_id: Chat ID
            inactive_days: Number of days the user has been inactive
        """
        try:
            # Create user mention
            user_mention = f"<a href='tg://user?id={user_id}'>Capo</a>"
            
            # Create warning message with mafia theming
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                warning_message = (
                    f"⚠️ *AVISO DE INACTIVIDAD* ⚠️\n\n"
                    f"{user_mention}, has estado inactivo por {inactive_days} días.\n\n"
                    f"La familia espera participación de todos sus miembros. "
                    f"Si no muestras actividad en las próximas 24 horas, "
                    f"serás removido del grupo."
                )
            else:
                warning_message = (
                    f"🔫 *¡DESPIERTA O DUERME CON LOS PECES!* 🔫\n\n"
                    f"{user_mention}, llevas {inactive_days} días sin contribuir a la familia.\n\n"
                    f"Don Hustle no está contento con tu falta de dedicación. "
                    f"Tienes 24 horas para mostrar señales de vida o "
                    f"te encontrarán flotando en el río."
                )
            
            # Send the warning
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=warning_message,
                parse_mode=ParseMode.HTML
            )
            
            logger.info(f"Sent inactivity warning to user {user_id} in chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending inactivity warning: {e}")
    
    async def _remove_inactive_user(self, user_id: int, chat_id: int):
        """
        Remove an inactive user from the chat
        
        Args:
            user_id: User ID to remove
            chat_id: Chat ID
        """
        try:
            # Try to kick the user
            await self.application.bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                until_date=datetime.now() + timedelta(seconds=35)  # Ban for 35 seconds (minimum time)
            )
            
            # Send notification about removal
            if self.theme_engine.get_tone() == ToneStyle.SERIOUS:
                removal_message = (
                    f"🚫 *MIEMBRO REMOVIDO POR INACTIVIDAD* 🚫\n\n"
                    f"Un miembro ha sido removido del grupo por inactividad prolongada.\n\n"
                    f"La familia valora la participación activa de todos sus miembros."
                )
            else:
                removal_message = (
                    f"🐟 *¡OTRO QUE DUERME CON LOS PECES!* 🐟\n\n"
                    f"Un miembro de la familia ha sido enviado a nadar con los peces por su inactividad.\n\n"
                    f"Don Hustle no tolera a quienes no contribuyen al negocio familiar."
                )
            
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=removal_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Removed inactive user {user_id} from chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error removing inactive user: {e}")
    
    def get_upcoming_reminders(self, chat_id: int, limit: int = 5) -> List[Reminder]:
        """
        Get upcoming reminders for a chat
        
        Args:
            chat_id: Chat ID to get reminders for
            limit: Maximum number of reminders to return
            
        Returns:
            List of upcoming Reminder objects
        """
        try:
            # Get all active reminders for the chat
            all_reminders = self.reminder_repository.get_active_reminders(chat_id)
            
            # Sort by remind_time
            sorted_reminders = sorted(all_reminders, key=lambda r: r.remind_time)
            
            # Return the first 'limit' reminders
            return sorted_reminders[:limit]
        except Exception as e:
            logger.error(f"Error getting upcoming reminders: {e}")
            return []


def setup_scheduler(application: Application, theme_engine: ThemeEngine):
    """
    Set up and start the bot scheduler
    
    Args:
        application: Telegram bot application
        theme_engine: ThemeEngine instance
        
    Returns:
        BotScheduler instance
    """
    scheduler = BotScheduler(application, theme_engine)
    
    # Check if job queue is available
    if application.job_queue is not None:
        # Start scheduler when bot starts (use async function instead of create_task)
        async def start_scheduler_callback(context):
            await scheduler.start()
        
        application.job_queue.run_once(start_scheduler_callback, when=10)
    else:
        # Start scheduler manually without job queue
        logger.warning("JobQueue not available. Scheduler will be started manually later.")
    
    # Register shutdown handler - we'll handle this in the main bot file instead
    # application.post_shutdown = scheduler.stop
    
    return scheduler