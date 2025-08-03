#!/usr/bin/env python3
"""
Simple Telegram Bot - Single File Implementation
Features:
- Basic message handling
- Command responses (/start, /help, /info)
- Inline keyboard with buttons
- Echo functionality
- Weather information (placeholder)
- User statistics tracking
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
except ImportError:
    print("Please install python-telegram-bot: pip install python-telegram-bot")
    exit(1)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        """Initialize the bot with token and user stats storage"""
        self.token = token
        self.application = Application.builder().token(token).build()
        self.user_stats = {}  # Simple in-memory storage
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("info", self.info_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("weather", self.weather_command))
        
        # Message handler for echo functionality
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo_message))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        # Update user stats
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'first_seen': datetime.now().isoformat(),
                'message_count': 0,
                'commands_used': 0
            }
        
        self.user_stats[user_id]['commands_used'] += 1
        
        # Create welcome message with inline keyboard
        keyboard = [
            [InlineKeyboardButton("ℹ️ Help", callback_data='help'),
             InlineKeyboardButton("📊 Stats", callback_data='stats')],
            [InlineKeyboardButton("🌤️ Weather", callback_data='weather'),
             InlineKeyboardButton("ℹ️ Info", callback_data='info')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🤖 Welcome to the Simple Telegram Bot!

Hello {user.first_name}! 👋

I'm a simple bot with basic features:
• Echo your messages
• Show weather information
• Track your usage statistics
• Provide helpful commands

Use the buttons below or type /help for more options!
        """.strip()
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **Available Commands:**

/start - Start the bot and show main menu
/help - Show this help message
/info - Show bot information
/stats - Show your usage statistics
/weather - Get weather information (placeholder)

**Features:**
• Echo functionality - I'll repeat your messages
• Inline keyboard buttons for easy navigation
• User statistics tracking
• Weather information (placeholder)

Just send me any message and I'll echo it back!
        """.strip()
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command"""
        info_text = """
🤖 **Bot Information:**

**Name:** Simple Telegram Bot
**Version:** 1.0.0
**Language:** Python
**Framework:** python-telegram-bot

**Features:**
✅ Message echo
✅ Command handling
✅ Inline keyboards
✅ User statistics
✅ Error handling

**Developer:** Created with ❤️ using python-telegram-bot

This is a single-file implementation demonstrating basic bot functionality.
        """.strip()
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id
        
        if user_id in self.user_stats:
            stats = self.user_stats[user_id]
            first_seen = datetime.fromisoformat(stats['first_seen']).strftime('%Y-%m-%d %H:%M:%S')
            
            stats_text = f"""
📊 **Your Statistics:**

👤 **User:** {update.effective_user.first_name}
📅 **First seen:** {first_seen}
💬 **Messages sent:** {stats['message_count']}
⌨️ **Commands used:** {stats['commands_used']}
📈 **Total interactions:** {stats['message_count'] + stats['commands_used']}
            """.strip()
        else:
            stats_text = "📊 No statistics available yet. Send some messages first!"
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /weather command (placeholder)"""
        weather_text = """
🌤️ **Weather Information**

This is a placeholder for weather functionality.

To implement real weather data, you would need to:
1. Sign up for a weather API (like OpenWeatherMap)
2. Add API key to environment variables
3. Make HTTP requests to get weather data
4. Parse and format the response

For now, here's some sample weather data:
📍 Location: Your City
🌡️ Temperature: 22°C
☁️ Condition: Partly Cloudy
💨 Wind: 15 km/h
💧 Humidity: 65%
        """.strip()
        
        await update.message.reply_text(weather_text, parse_mode='Markdown')
    
    async def echo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Echo user messages and update stats"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Update user stats
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'first_seen': datetime.now().isoformat(),
                'message_count': 0,
                'commands_used': 0
            }
        
        self.user_stats[user_id]['message_count'] += 1
        
        # Echo the message with some formatting
        echo_text = f"🔄 **Echo:** {message_text}"
        await update.message.reply_text(echo_text, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button callbacks"""
        query = update.callback_query
        await query.answer()  # Answer the callback query
        
        if query.data == 'help':
            await self.help_command(update, context)
        elif query.data == 'stats':
            await self.stats_command(update, context)
        elif query.data == 'weather':
            await self.weather_command(update, context)
        elif query.data == 'info':
            await self.info_command(update, context)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Sorry, something went wrong. Please try again later."
            )
    
    def run(self):
        """Start the bot"""
        print("🤖 Starting Telegram Bot...")
        print("Press Ctrl+C to stop the bot")
        
        try:
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            print(f"❌ Error running bot: {e}")

def main():
    """Main function to run the bot"""
    # Get bot token from environment variable or user input
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("🤖 Telegram Bot Setup")
        print("=" * 30)
        print("You need a bot token from @BotFather on Telegram")
        print("1. Message @BotFather on Telegram")
        print("2. Send /newbot")
        print("3. Follow the instructions")
        print("4. Copy the token you receive")
        print()
        
        token = input("Enter your bot token: ").strip()
        
        if not token:
            print("❌ No token provided. Exiting.")
            return
    
    # Create and run the bot
    bot = TelegramBot(token)
    bot.run()

if __name__ == "__main__":
    main()