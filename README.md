# Telegram Bot for Anonymous Market Offers

A Telegram bot built with Python, Flask, and `python-telegram-bot` that allows users to submit anonymous offers for coins, gold, and foreign currency.

## Features

- Multi-step conversation flow
- Anonymous offer submission
- Support for coins, melted gold, and foreign currency
- Inline confirmation buttons
- Admin notifications
- Channel message publishing
- Flask-based webhook support
- Environment variable configuration for sensitive data

## Technologies

- Python
- Flask
- python-telegram-bot
- Telegram Bot API
- Webhooks

## Environment Variables

The application requires the following environment variables:

- `BOT_TOKEN`
- `CHANNEL_ID`
- `ADMIN_ID`

For security reasons, these values should be stored in a `.env` file or configured directly in the deployment environment.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Then configure the required environment variables and run:

```bash
python bot.py
```

## Deployment

The project includes a `Procfile` for web deployment:

```text
web: python bot.py
```

## Security

Sensitive information such as the Telegram bot token and IDs are not stored directly in the source code. They are loaded from environment variables.

## Future Improvements

- Persistent database storage
- Better input validation
- Improved access control for confirmation actions
- Logging and error handling
- Automated tests
