# Simple Telegram Bot

A lightweight, single-file Telegram bot built with Python and aiohttp. This bot provides basic functionality including echo commands, user information, and interactive messaging.

## Features

- 🤖 **Simple Commands**: `/start`, `/help`, `/echo`, `/info`
- 💬 **Interactive Messaging**: Responds to all text messages
- 📋 **User Information**: Display chat and user details
- 🔄 **Echo Functionality**: Echo back user messages
- ⚡ **Async Performance**: Built with async/await for better performance
- 📦 **Single File**: Everything contained in one `bot.py` file
- 🛡️ **Error Handling**: Robust error handling and logging

## Requirements

- Python 3.7 or higher
- `aiohttp` library
- Telegram Bot Token (from @BotFather)

## Quick Setup

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a Telegram bot**:
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` and follow the instructions
   - Copy your bot token

4. **Set environment variable**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

5. **Run the bot**:
   ```bash
   python bot.py
   ```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome message and bot introduction | `/start` |
| `/help` | Show help information and available commands | `/help` |
| `/echo [text]` | Echo back the provided text | `/echo Hello World!` |
| `/info` | Display user and chat information | `/info` |

## Bot Functionality

### Basic Interaction
- Send any text message and the bot will echo it back with a friendly response
- All responses include helpful formatting and emojis for better user experience

### User Information
- The `/info` command displays detailed information about the user and chat
- Includes user ID, name, username, language, chat type, and message details

### Echo Feature
- Use `/echo` followed by text to have the bot repeat your message
- Supports emojis, special characters, and formatting

### Error Handling
- Unknown commands receive a helpful error message
- Failed operations are logged and handled gracefully
- Users are notified if something goes wrong

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Your bot token from @BotFather |

## File Structure

```
.
├── bot.py              # Main bot file (single file implementation)
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Technical Details

- **Async Framework**: Uses `aiohttp` for HTTP requests to Telegram API
- **Polling Method**: Long polling for receiving updates (30-second timeout)
- **Error Recovery**: Automatic retry logic for failed API calls
- **Logging**: Comprehensive logging for debugging and monitoring

## Customization

The bot is designed to be easily customizable. You can:

1. **Add new commands** by creating new handler methods
2. **Modify responses** by editing the text in handler methods
3. **Add features** like database storage, webhooks, or additional APIs
4. **Change styling** by modifying the emoji and formatting in messages

## Example Usage

```bash
# Set your bot token
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

# Run the bot
python bot.py
```

Once running, you can interact with your bot on Telegram:

```
User: /start
Bot: 🤖 Hello User! Welcome to this simple Telegram bot! Here's what I can do: ...

User: /echo Hello World! 🎉
Bot: 🔄 Echo: Hello World! 🎉

User: How are you?
Bot: 💬 Hi User! You said: How are you? 🤖 Use /help to see available commands!
```

## Troubleshooting

### Common Issues

1. **"TELEGRAM_BOT_TOKEN not set" error**:
   - Make sure you've exported the environment variable
   - Check that your token is correct and doesn't have extra spaces

2. **"Failed to get updates" error**:
   - Check your internet connection
   - Verify your bot token is valid
   - Ensure the bot isn't already running elsewhere

3. **Bot not responding**:
   - Check the console for error messages
   - Verify the bot is running with `python bot.py`
   - Try restarting the bot

### Debug Mode

The bot includes comprehensive logging. Check the console output for detailed information about:
- Received messages
- API calls
- Errors and exceptions
- User interactions

## Contributing

Feel free to fork this project and submit pull requests for:
- New features
- Bug fixes
- Documentation improvements
- Performance optimizations

## License

This project is open source and available under the MIT License.

---

**Need help?** Feel free to open an issue or contact the maintainers!