#!/usr/bin/env python3
"""
Simple Telegram Bot - All in one file
A basic Telegram bot that responds to messages and commands.
"""

import logging
import os
import asyncio
from typing import Optional
import aiohttp
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, data: dict = None) -> dict:
        """Make an HTTP request to Telegram API"""
        url = f"{self.base_url}/{method}"
        try:
            async with self.session.post(url, json=data) as response:
                result = await response.json()
                if not result.get('ok'):
                    logger.error(f"API Error: {result}")
                return result
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"ok": False, "error": str(e)}
    
    async def send_message(self, chat_id: int, text: str, reply_to_message_id: int = None) -> dict:
        """Send a text message to a chat"""
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        
        return await self.make_request("sendMessage", data)
    
    async def get_updates(self, timeout: int = 30) -> dict:
        """Get updates from Telegram"""
        data = {
            "offset": self.offset,
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"]
        }
        return await self.make_request("getUpdates", data)
    
    async def handle_start_command(self, message: dict):
        """Handle /start command"""
        chat_id = message["chat"]["id"]
        user_name = message["from"].get("first_name", "User")
        
        welcome_text = f"""
🤖 <b>Hello {user_name}!</b>

Welcome to this simple Telegram bot! Here's what I can do:

📋 <b>Available Commands:</b>
/start - Show this welcome message
/help - Get help information
/echo [text] - Echo back your text
/info - Get your chat information

💬 <b>Other Features:</b>
• Send me any message and I'll echo it back
• I can handle text, emojis, and basic formatting

Try sending me a message or use one of the commands above!
        """
        
        await self.send_message(chat_id, welcome_text)
    
    async def handle_help_command(self, message: dict):
        """Handle /help command"""
        chat_id = message["chat"]["id"]
        
        help_text = """
🆘 <b>Bot Help</b>

<b>Commands:</b>
/start - Welcome message
/help - This help message
/echo [text] - Echo your text
/info - Your chat info

<b>Usage Examples:</b>
• <code>/echo Hello World!</code>
• Just send any text message
• Send emojis: 🎉🚀⭐

<b>Support:</b>
This is a simple demo bot. Feel free to experiment!
        """
        
        await self.send_message(chat_id, help_text)
    
    async def handle_echo_command(self, message: dict):
        """Handle /echo command"""
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        
        # Extract text after /echo command
        echo_text = text[5:].strip()  # Remove "/echo" prefix
        
        if not echo_text:
            await self.send_message(chat_id, "📢 Please provide text to echo!\nExample: <code>/echo Hello World!</code>")
            return
        
        response = f"🔄 <b>Echo:</b> {echo_text}"
        await self.send_message(chat_id, response, reply_to_message_id=message["message_id"])
    
    async def handle_info_command(self, message: dict):
        """Handle /info command"""
        chat_id = message["chat"]["id"]
        user = message["from"]
        chat = message["chat"]
        
        info_text = f"""
ℹ️ <b>Chat Information</b>

👤 <b>User Info:</b>
• Name: {user.get('first_name', 'N/A')} {user.get('last_name', '')}
• Username: @{user.get('username', 'N/A')}
• User ID: <code>{user.get('id')}</code>
• Language: {user.get('language_code', 'N/A')}

💬 <b>Chat Info:</b>
• Chat ID: <code>{chat.get('id')}</code>
• Chat Type: {chat.get('type', 'N/A')}

🕐 <b>Message Info:</b>
• Message ID: {message.get('message_id')}
• Date: {message.get('date')}
        """
        
        await self.send_message(chat_id, info_text)
    
    async def handle_regular_message(self, message: dict):
        """Handle regular text messages"""
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        user_name = message["from"].get("first_name", "User")
        
        # Simple echo with a friendly response
        response = f"💬 Hi {user_name}! You said: <i>{text}</i>\n\n🤖 Use /help to see available commands!"
        
        await self.send_message(chat_id, response, reply_to_message_id=message["message_id"])
    
    async def handle_message(self, message: dict):
        """Process incoming messages"""
        try:
            text = message.get("text", "").strip()
            
            if text.startswith("/start"):
                await self.handle_start_command(message)
            elif text.startswith("/help"):
                await self.handle_help_command(message)
            elif text.startswith("/echo"):
                await self.handle_echo_command(message)
            elif text.startswith("/info"):
                await self.handle_info_command(message)
            elif text.startswith("/"):
                # Unknown command
                chat_id = message["chat"]["id"]
                await self.send_message(chat_id, "❓ Unknown command. Use /help to see available commands.")
            else:
                # Regular message
                await self.handle_regular_message(message)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            chat_id = message["chat"]["id"]
            await self.send_message(chat_id, "😅 Sorry, something went wrong processing your message.")
    
    async def run(self):
        """Main bot loop"""
        logger.info("Bot started! Press Ctrl+C to stop.")
        
        try:
            while True:
                # Get updates from Telegram
                updates = await self.get_updates()
                
                if not updates.get("ok"):
                    logger.error("Failed to get updates")
                    await asyncio.sleep(5)
                    continue
                
                results = updates.get("result", [])
                
                for update in results:
                    # Update offset to avoid getting the same update twice
                    self.offset = update["update_id"] + 1
                    
                    # Handle message updates
                    if "message" in update:
                        message = update["message"]
                        logger.info(f"Received message from {message['from'].get('first_name', 'Unknown')}: {message.get('text', '[non-text]')}")
                        await self.handle_message(message)
                
                # Small delay to avoid overwhelming the API
                if not results:
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise

async def main():
    """Main function to run the bot"""
    # Get bot token from environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable not set!")
        print("\n📋 To use this bot:")
        print("1. Create a bot with @BotFather on Telegram")
        print("2. Get your bot token")
        print("3. Set environment variable: export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("4. Run the bot: python bot.py")
        return
    
    # Create and run the bot
    async with TelegramBot(token) as bot:
        await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")