# Telegram-Bot
# Test_maryambot

Telegram Anonymous Messaging Bot built with Python, aiogram 3, and SQLAlchemy Async.

## Features

- User registration via `/start`
- Generate personal link for receiving messages
- Send and receive anonymous messages
- Reply anonymously
- Inbox management
- Block/unblock users
- Report users and automatic suspension after repeated reports
- Daily message limits and scoring system
- VIP subscription with extended features
- Support messaging
- Admin commands for management
- Supports SQLite and PostgreSQL

> Note: Telegram Bot API does not allow sending messages to users who haven't started the bot.

## Setup

1. Extract the project and enter the folder:

```bash
cd C:\bots\Test_maryambot
```

2. Create virtual environment:

```bash
python -m venv venv
```

3. Install dependencies:

```bash
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Configure environment:

```bash
copy .env.example .env
notepad .env
```

Set your bot token, admin IDs, username, and database URL.

5. Run the bot:

```bash
venv\Scripts\python.exe -m app.main
```

## Admin Commands

```text
/stats                  # Show users and tickets
/answer TICKET_ID text  # Reply to support ticket
/vip TELEGRAM_ID DAYS    # Activate VIP for a user
```

## License

MIT License
