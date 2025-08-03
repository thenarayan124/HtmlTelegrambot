#!/usr/bin/env python3
"""
Telegram Bot - Single File Implementation
A comprehensive Telegram bot with multiple features
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        """Initialize the Telegram bot with API token"""
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.commands = {
            '/start': self.handle_start,
            '/help': self.handle_help,
            '/echo': self.handle_echo,
            '/time': self.handle_time,
            '/weather': self.handle_weather,
            '/joke': self.handle_joke,
            '/menu': self.handle_menu,
            '/info': self.handle_info
        }
        
    def get_updates(self) -> Dict[str, Any]:
        """Get updates from Telegram API"""
        try:
            params = {'offset': self.offset, 'timeout': 30}
            response = requests.get(f"{self.base_url}/getUpdates", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting updates: {e}")
            return {'ok': False, 'result': []}
    
    def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict] = None) -> bool:
        """Send a message to a specific chat"""
        try:
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            if reply_markup:
                data['reply_markup'] = json.dumps(reply_markup)
            
            response = requests.post(f"{self.base_url}/sendMessage", json=data)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_photo(self, chat_id: int, photo_url: str, caption: str = "") -> bool:
        """Send a photo to a specific chat"""
        try:
            data = {
                'chat_id': chat_id,
                'photo': photo_url,
                'caption': caption
            }
            response = requests.post(f"{self.base_url}/sendPhoto", json=data)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Error sending photo: {e}")
            return False
    
    def create_inline_keyboard(self, buttons: list) -> Dict[str, Any]:
        """Create an inline keyboard markup"""
        return {
            'inline_keyboard': buttons
        }
    
    def create_reply_keyboard(self, buttons: list, one_time: bool = True) -> Dict[str, Any]:
        """Create a reply keyboard markup"""
        return {
            'keyboard': buttons,
            'one_time_keyboard': one_time,
            'resize_keyboard': True
        }
    
    # Command handlers
    def handle_start(self, chat_id: int, message: str) -> None:
        """Handle /start command"""
        welcome_text = """
🤖 <b>Welcome to the Telegram Bot!</b>

I'm a multi-feature bot that can help you with various tasks.

<b>Available commands:</b>
• /start - Show this welcome message
• /help - Show help information
• /echo [text] - Echo back your message
• /time - Show current time
• /weather [city] - Get weather information
• /joke - Get a random joke
• /menu - Show interactive menu
• /info - Show bot information

Try sending me a command or just chat with me!
        """
        self.send_message(chat_id, welcome_text.strip())
    
    def handle_help(self, chat_id: int, message: str) -> None:
        """Handle /help command"""
        help_text = """
📚 <b>Bot Help Guide</b>

<b>Basic Commands:</b>
• /start - Start the bot and see welcome message
• /help - Show this help information

<b>Utility Commands:</b>
• /echo [text] - I'll repeat what you say
• /time - Get current date and time
• /info - Learn more about this bot

<b>Fun Commands:</b>
• /joke - Get a random joke
• /weather [city] - Get weather forecast
• /menu - Interactive menu with buttons

<b>Examples:</b>
• /echo Hello world
• /weather London
• /joke

Just type any command to get started!
        """
        self.send_message(chat_id, help_text.strip())
    
    def handle_echo(self, chat_id: int, message: str) -> None:
        """Handle /echo command"""
        if len(message.split()) > 1:
            echo_text = ' '.join(message.split()[1:])
            self.send_message(chat_id, f"🔄 <b>Echo:</b> {echo_text}")
        else:
            self.send_message(chat_id, "❌ Please provide text to echo. Example: /echo Hello world")
    
    def handle_time(self, chat_id: int, message: str) -> None:
        """Handle /time command"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_text = f"🕐 <b>Current Time:</b>\n{current_time}"
        self.send_message(chat_id, time_text)
    
    def handle_weather(self, chat_id: int, message: str) -> None:
        """Handle /weather command"""
        if len(message.split()) > 1:
            city = ' '.join(message.split()[1:])
            # This is a mock weather response - in a real bot you'd use a weather API
            weather_text = f"🌤️ <b>Weather for {city}:</b>\n\n"
            weather_text += "☀️ Temperature: 22°C\n"
            weather_text += "💨 Wind: 15 km/h\n"
            weather_text += "💧 Humidity: 65%\n"
            weather_text += "☁️ Condition: Partly cloudy\n\n"
            weather_text += "<i>Note: This is mock data. For real weather, integrate with a weather API.</i>"
            self.send_message(chat_id, weather_text)
        else:
            self.send_message(chat_id, "❌ Please provide a city name. Example: /weather London")
    
    def handle_joke(self, chat_id: int, message: str) -> None:
        """Handle /joke command"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything! 🤓",
            "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
            "Why don't eggs tell jokes? They'd crack each other up! 🥚",
            "What do you call a fake noodle? An impasta! 🍝",
            "Why did the math book look so sad? Because it had too many problems! 📚",
            "What do you call a bear with no teeth? A gummy bear! 🐻",
            "Why don't skeletons fight each other? They don't have the guts! 💀",
            "What do you call a fish wearing a bowtie? So-fish-ticated! 🐟"
        ]
        import random
        joke = random.choice(jokes)
        self.send_message(chat_id, f"😄 <b>Random Joke:</b>\n\n{joke}")
    
    def handle_menu(self, chat_id: int, message: str) -> None:
        """Handle /menu command"""
        keyboard = self.create_inline_keyboard([
            [{'text': '🕐 Get Time', 'callback_data': 'time'}],
            [{'text': '😄 Get Joke', 'callback_data': 'joke'}],
            [{'text': '🌤️ Weather', 'callback_data': 'weather'}],
            [{'text': 'ℹ️ Bot Info', 'callback_data': 'info'}]
        ])
        self.send_message(chat_id, "🎛️ <b>Interactive Menu</b>\n\nChoose an option:", keyboard)
    
    def handle_info(self, chat_id: int, message: str) -> None:
        """Handle /info command"""
        info_text = """
ℹ️ <b>Bot Information</b>

🤖 <b>Bot Name:</b> Multi-Feature Telegram Bot
📅 <b>Created:</b> 2024
🔧 <b>Language:</b> Python
📚 <b>Features:</b> Commands, Inline Keyboards, Message Handling

<b>Developer:</b> AI Assistant
<b>Version:</b> 1.0.0

This bot demonstrates various Telegram Bot API features including:
• Command handling
• Inline keyboards
• Message responses
• Error handling
• Logging

Feel free to explore all the features!
        """
        self.send_message(chat_id, info_text.strip())
    
    def handle_callback_query(self, callback_query: Dict[str, Any]) -> None:
        """Handle callback queries from inline keyboards"""
        chat_id = callback_query['message']['chat']['id']
        callback_data = callback_query['data']
        
        if callback_data == 'time':
            self.handle_time(chat_id, '/time')
        elif callback_data == 'joke':
            self.handle_joke(chat_id, '/joke')
        elif callback_data == 'weather':
            self.send_message(chat_id, "🌤️ <b>Weather</b>\n\nPlease use /weather [city] to get weather information.")
        elif callback_data == 'info':
            self.handle_info(chat_id, '/info')
        
        # Answer callback query to remove loading state
        try:
            requests.post(f"{self.base_url}/answerCallbackQuery", json={
                'callback_query_id': callback_query['id']
            })
        except requests.RequestException as e:
            logger.error(f"Error answering callback query: {e}")
    
    def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming messages"""
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        # Handle commands
        if text.startswith('/'):
            command = text.split()[0].lower()
            if command in self.commands:
                self.commands[command](chat_id, text)
            else:
                self.send_message(chat_id, f"❌ Unknown command: {command}\nUse /help to see available commands.")
        else:
            # Handle regular messages
            if text.lower() in ['hello', 'hi', 'hey']:
                self.send_message(chat_id, f"👋 Hello! How can I help you today? Use /help to see what I can do!")
            elif 'how are you' in text.lower():
                self.send_message(chat_id, "😊 I'm doing great, thanks for asking! How about you?")
            elif 'bye' in text.lower() or 'goodbye' in text.lower():
                self.send_message(chat_id, "👋 Goodbye! Feel free to come back anytime!")
            else:
                self.send_message(chat_id, f"💬 You said: <i>{text}</i>\n\nTry using /help to see what commands I understand!")
    
    def run(self) -> None:
        """Main bot loop"""
        logger.info("Bot started. Press Ctrl+C to stop.")
        
        try:
            while True:
                updates = self.get_updates()
                
                if updates.get('ok') and updates['result']:
                    for update in updates['result']:
                        self.offset = update['update_id'] + 1
                        
                        if 'message' in update:
                            self.handle_message(update['message'])
                        elif 'callback_query' in update:
                            self.handle_callback_query(update['callback_query'])
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

def main():
    """Main function to run the bot"""
    # Get token from environment variable or user input
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("🤖 Telegram Bot Setup")
        print("=" * 30)
        print("To use this bot, you need a Telegram Bot Token.")
        print("1. Message @BotFather on Telegram")
        print("2. Create a new bot with /newbot")
        print("3. Copy the token and set it as environment variable:")
        print("   export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("\nOr enter your token below:")
        token = input("Bot Token: ").strip()
        
        if not token:
            print("❌ No token provided. Exiting.")
            return
    
    # Create and run the bot
    bot = TelegramBot(token)
    
    # Test the connection
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                print(f"✅ Bot connected successfully!")
                print(f"🤖 Bot name: {bot_info['result']['first_name']}")
                print(f"👤 Username: @{bot_info['result']['username']}")
                print("\n🚀 Starting bot...")
                bot.run()
            else:
                print("❌ Invalid bot token.")
        else:
            print("❌ Failed to connect to Telegram API.")
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    main()