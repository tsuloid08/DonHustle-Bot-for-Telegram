-- Database schema for @donhustle_bot
-- Mafia-themed Telegram bot with group management features

-- Quotes table for motivational messages
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Saved messages table for tagged and important messages
CREATE TABLE IF NOT EXISTS saved_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    tag TEXT,
    saved_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reminders table for scheduled notifications
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    remind_time TIMESTAMP NOT NULL,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User activity table for tracking inactive users
CREATE TABLE IF NOT EXISTS user_activity (
    user_id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0
);

-- Custom commands table for user-defined bot commands
CREATE TABLE IF NOT EXISTS custom_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    command_name TEXT NOT NULL,
    response TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id, command_name)
);

-- Configuration table for bot settings per chat
CREATE TABLE IF NOT EXISTS config (
    chat_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (chat_id, key)
);

-- Spam filters table for anti-spam moderation
CREATE TABLE IF NOT EXISTS spam_filters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    filter_word TEXT NOT NULL,
    action TEXT DEFAULT 'warn',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_saved_messages_chat_id ON saved_messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_saved_messages_tag ON saved_messages(tag);
CREATE INDEX IF NOT EXISTS idx_reminders_chat_id ON reminders(chat_id);
CREATE INDEX IF NOT EXISTS idx_reminders_remind_time ON reminders(remind_time);
CREATE INDEX IF NOT EXISTS idx_user_activity_chat_id ON user_activity(chat_id);
CREATE INDEX IF NOT EXISTS idx_custom_commands_chat_id ON custom_commands(chat_id);
CREATE INDEX IF NOT EXISTS idx_spam_filters_chat_id ON spam_filters(chat_id);