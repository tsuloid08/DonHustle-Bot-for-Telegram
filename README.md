# @donhustle_bot - Telegram Mafia-Themed Group Management Bot

A powerful Telegram bot with a mafia-inspired theme for managing private groups with advanced moderation, automation, and organization features.

## Features

- 🎭 **Mafia-themed personality** with charismatic, authoritative responses
- 📝 **Quote management system** with file upload support (.txt, .csv, .json)
- 🏷️ **Message tagging and saving** for important content organization
- ⏰ **Reminder system** with recurring reminder support
- 👥 **Inactive user management** with automatic warnings and removal
- 🛡️ **Anti-spam and moderation** with customizable filters
- ⚙️ **Custom commands** for personalized functionality
- 🎨 **Configurable bot style** (serious/humorous tone)

## Setup

### 1. Get Your Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Choose a name and username for your bot
4. Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Configure the Bot
1. Clone this repository
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and replace `your_bot_token_here` with your actual bot token:
   ```
   BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

### 3. Install and Run
1. Install dependencies: `pip install -r requirements.txt`
2. Run the bot: `python bot.py`

The bot will automatically validate your token format and provide helpful error messages if there are issues.

## Project Structure

```
├── bot.py              # Main bot application
├── handlers/           # Command and message handlers
├── database/           # Database models and repositories
├── utils/              # File processing, scheduling, theme engine
├── tests/              # Unit and integration tests
├── requirements.txt    # Python dependencies
└── .env.example       # Environment variables template
```

## Requirements

- Python 3.8+
- Telegram Bot Token (from @BotFather)
- SQLite (included with Python)

## License

This project is licensed under the MIT License.