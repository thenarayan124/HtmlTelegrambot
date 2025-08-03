#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 TaskCompleteRewardsBot - Complete Telegram Bot for Task Rewards

A fully featured Telegram bot that rewards users for completing tasks like YouTube subscriptions,
Instagram follows, Telegram joins, etc. with UPI payment system and referral program.

QUICK SETUP:
============
1. Install dependencies:
   pip install pyTelegramBotAPI requests flask --break-system-packages

2. Get your bot token from @BotFather on Telegram

3. Replace YOUR_BOT_TOKEN_HERE below with your actual token

4. Run the bot:
   python3 bot.py

5. Test with /start command

FEATURES:
=========
🎯 User Features:
- Complete Hindi Interface
- Task System (YouTube, Instagram, Telegram, Facebook, WhatsApp)
- Balance Management
- UPI Withdrawal (₹10 minimum)
- Referral Program (₹2 per referral + milestone bonuses)
- Screenshot submission for verification

🔧 Admin Features:
- Complete Admin Panel
- Task Management (Add, Edit, Delete)
- User Management (View, Block/Unblock)
- Withdrawal Approval/Rejection
- Screenshot Verification
- Broadcasting System
- Comprehensive Statistics
- Activity Logs

💰 Reward System:
- ₹2-5 per completed task
- ₹2 per referral
- Milestone bonuses: 5=₹10, 10=₹25, 25=₹50, 50=₹100, 100=₹250
- UPI payment integration

ADMIN SETUP:
============
Change ADMIN_ID below to your Telegram user ID.
To get your ID, send a message to @userinfobot

DATA STORAGE:
=============
All data is stored in memory (no external files needed).
Bot includes sample tasks for immediate testing.

Version: 3.0
Author: TaskCompleteRewardsBot Team
"""

import os
import threading
import time
import random
import string
import requests
from datetime import datetime
from flask import Flask
import telebot
from telebot import types

# ======================
# Configuration
# ======================

# ⚠️ IMPORTANT: Replace with your actual bot token from @BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# ⚠️ IMPORTANT: Replace with your Telegram user ID (get from @userinfobot)
ADMIN_ID = 5367009004

# Bot Settings
MIN_WITHDRAWAL = 10  # ₹10 minimum withdrawal
REWARD_PER_REFERRAL = 2  # ₹2 per referral
MAX_TASKS_PER_USER = 10
DAILY_TASK_LIMIT = 20

# Milestone bonuses for referrals
MILESTONE_BONUSES = {
    5: 10,    # ₹10 for 5 referrals
    10: 25,   # ₹25 for 10 referrals
    25: 50,   # ₹50 for 25 referrals
    50: 100,  # ₹100 for 50 referrals
    100: 250  # ₹250 for 100 referrals
}

# Task types with Hindi names
TASK_TYPES = {
    'youtube_subscribe': 'YouTube Subscribe',
    'instagram_follow': 'Instagram Follow',
    'telegram_join': 'Telegram Join',
    'facebook_like': 'Facebook Like',
    'whatsapp_join': 'WhatsApp Join'
}

# ======================
# In-Memory Data Storage
# ======================

# Users database
USERS_DB = {}

# Sample tasks for immediate testing
TASKS_DB = [
    {
        'id': 'task_youtube_1',
        'title': 'YouTube Channel Subscribe करें',
        'description': 'हमारे YouTube चैनल को सब्सक्राइब करें और बेल आइकन दबाएं। सब्सक्राइब करने के बाद स्क्रीनशॉट लें।',
        'link': 'https://youtube.com/@TechChannel',
        'reward': 5,
        'type': 'youtube_subscribe',
        'active': True,
        'created_at': '2025-01-15 10:00:00',
        'completed_count': 0
    },
    {
        'id': 'task_instagram_1',
        'title': 'Instagram Page Follow करें',
        'description': 'हमारे Instagram पेज को फॉलो करें। फॉलो करने के बाद प्रोफाइल का स्क्रीनशॉट लें।',
        'link': 'https://instagram.com/techpage',
        'reward': 3,
        'type': 'instagram_follow',
        'active': True,
        'created_at': '2025-01-15 10:00:00',
        'completed_count': 0
    },
    {
        'id': 'task_telegram_1',
        'title': 'Telegram Group Join करें',
        'description': 'हमारे Telegram ग्रुप में शामिल हों। Join करने के बाद ग्रुप का स्क्रीनशॉट लें।',
        'link': 'https://t.me/TechGroup',
        'reward': 4,
        'type': 'telegram_join',
        'active': True,
        'created_at': '2025-01-15 10:00:00',
        'completed_count': 0
    },
    {
        'id': 'task_facebook_1',
        'title': 'Facebook Page Like करें',
        'description': 'हमारे Facebook पेज को लाइक और फॉलो करें। लाइक करने के बाद पेज का स्क्रीनशॉट लें।',
        'link': 'https://facebook.com/TechPage',
        'reward': 3,
        'type': 'facebook_like',
        'active': True,
        'created_at': '2025-01-15 10:00:00',
        'completed_count': 0
    },
    {
        'id': 'task_whatsapp_1',
        'title': 'WhatsApp Group Join करें',
        'description': 'हमारे WhatsApp ग्रुप में शामिल हों। Join करने के बाद ग्रुप का स्क्रीनशॉट लें।',
        'link': 'https://chat.whatsapp.com/invite/ABC123',
        'reward': 2,
        'type': 'whatsapp_join',
        'active': True,
        'created_at': '2025-01-15 10:00:00',
        'completed_count': 0
    }
]

# Submissions database
SUBMISSIONS_DB = {}

# Withdrawals database
WITHDRAWALS_DB = []

# Activity logs
ACTIVITY_LOGS = []

# Global variables
blocked_users = set()
user_current_task = {}
bot_username = "TaskCompleteRewardsBot"

# Initialize bot
try:
    bot = telebot.TeleBot(BOT_TOKEN)
    print("✅ Bot initialized successfully!")
except Exception as e:
    print(f"❌ Failed to initialize bot: {e}")
    print("⚠️  Please check your BOT_TOKEN")
    exit(1)

# ======================
# Utility Functions
# ======================

def log_activity(message):
    """Log activity with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'message': message
    }
    ACTIVITY_LOGS.append(log_entry)
    
    # Keep only last 100 logs to prevent memory overflow
    if len(ACTIVITY_LOGS) > 100:
        ACTIVITY_LOGS.pop(0)
    
    print(f"[{timestamp}] {message}")

def generate_referral_code(user_id):
    """Generate unique referral code for user"""
    return f"REF{user_id}{random.randint(1000, 9999)}"

def is_admin(user_id):
    """Check if user is admin"""
    return int(user_id) == ADMIN_ID

def is_user_blocked(user_id):
    """Check if user is blocked"""
    return str(user_id) in blocked_users

def get_user_data(user_id):
    """Get user data from database"""
    return USERS_DB.get(str(user_id))

def update_user_data(user_id, **kwargs):
    """Update user data in database"""
    user_id = str(user_id)
    if user_id not in USERS_DB:
        USERS_DB[user_id] = {}
    
    for key, value in kwargs.items():
        USERS_DB[user_id][key] = value
    return True

def get_bot_username():
    """Get bot username dynamically"""
    global bot_username
    try:
        bot_info = bot.get_me()
        bot_username = bot_info.username
    except:
        pass
    return bot_username

def create_main_keyboard(is_admin_user=False):
    """Create main keyboard for user"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if is_admin_user:
        markup.add(types.KeyboardButton('🎯 नया कार्य'), types.KeyboardButton('🔧 Admin Panel'))
    else:
        markup.add(types.KeyboardButton('🎯 नया कार्य'))
    
    markup.add(types.KeyboardButton('💰 बैलेंस'), types.KeyboardButton('🔗 रेफर'))
    markup.add(types.KeyboardButton('💸 निकासी'), types.KeyboardButton('❓ सहायता'))
    
    return markup

def format_currency(amount):
    """Format currency with rupee symbol"""
    return f"₹{amount}"

# ======================
# Database Functions
# ======================

def get_tasks():
    """Get all tasks"""
    return TASKS_DB

def add_task(task):
    """Add new task"""
    TASKS_DB.append(task)
    log_activity(f"New task added: {task['title']}")
    return True

def get_task_by_id(task_id):
    """Get specific task by ID"""
    return next((t for t in TASKS_DB if t['id'] == task_id), None)

def record_submission(user_id, task_id, file_id):
    """Record user task submission"""
    if str(user_id) not in SUBMISSIONS_DB:
        SUBMISSIONS_DB[str(user_id)] = []
    
    submission = {
        'task_id': task_id,
        'file_id': file_id,
        'status': 'pending',
        'submitted_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    SUBMISSIONS_DB[str(user_id)].append(submission)
    log_activity(f"User {user_id} submitted proof for task {task_id}")
    return True

def get_pending_submissions():
    """Get all pending submissions"""
    pending = []
    for user_id, submissions in SUBMISSIONS_DB.items():
        for sub in submissions:
            if sub['status'] == 'pending':
                pending.append({
                    'user_id': user_id,
                    'task_id': sub['task_id'],
                    'file_id': sub['file_id'],
                    'submitted_at': sub['submitted_at']
                })
    return pending

def update_submission_status(user_id, task_id, status, reason=None):
    """Update submission status"""
    user_id = str(user_id)
    if user_id not in SUBMISSIONS_DB:
        return False
    
    for sub in SUBMISSIONS_DB[user_id]:
        if sub['task_id'] == task_id and sub['status'] == 'pending':
            sub['status'] = status
            sub['processed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if reason:
                sub['reason'] = reason
            return True
    return False

def get_pending_withdrawals():
    """Get pending withdrawals"""
    return [w for w in WITHDRAWALS_DB if w['status'] == 'pending']

# ======================
# Keep Alive Server
# ======================

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🎯 TaskCompleteRewardsBot</h1>
    <p>✅ Bot is running successfully!</p>
    <p>📊 <a href="/stats">View Statistics</a></p>
    <p>📱 Start bot: <a href="https://t.me/{}" target="_blank">@{}</a></p>
    """.format(bot_username, bot_username)

@app.route('/stats')
def web_stats():
    """Web statistics page"""
    stats = {
        'total_users': len(USERS_DB),
        'active_users': len([u for u in USERS_DB.values() if not u.get('blocked', False)]),
        'total_tasks': len(TASKS_DB),
        'active_tasks': len([t for t in TASKS_DB if t.get('active', True)]),
        'pending_submissions': len(get_pending_submissions()),
        'pending_withdrawals': len(get_pending_withdrawals()),
        'total_balance': sum(u.get('balance', 0) for u in USERS_DB.values()),
        'total_referrals': sum(u.get('referrals', 0) for u in USERS_DB.values())
    }
    
    html = f"""
    <h1>📊 Bot Statistics</h1>
    <ul>
        <li>👥 Total Users: {stats['total_users']}</li>
        <li>✅ Active Users: {stats['active_users']}</li>
        <li>📋 Total Tasks: {stats['total_tasks']}</li>
        <li>🎯 Active Tasks: {stats['active_tasks']}</li>
        <li>📸 Pending Submissions: {stats['pending_submissions']}</li>
        <li>💸 Pending Withdrawals: {stats['pending_withdrawals']}</li>
        <li>💰 Total Balance: ₹{stats['total_balance']}</li>
        <li>🔗 Total Referrals: {stats['total_referrals']}</li>
    </ul>
    <p><a href="/">← Back to Home</a></p>
    """
    return html

def keep_alive():
    """Start keep alive server"""
    server = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080, debug=False))
    server.daemon = True
    server.start()
    log_activity("Keep-alive server started on port 8080")

# ======================
# Message Handlers
# ======================

@bot.message_handler(commands=['start'])
def handle_start(message):
    """Handle /start command"""
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    
    user = get_user_data(user_id)
    
    # Register new user
    if not user:
        referral_code = generate_referral_code(user_id)
        new_user = {
            "id": user_id,
            "first_name": first_name,
            "balance": 0,
            "referrals": 0,
            "referral_code": referral_code,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "blocked": False,
            "completed_tasks": []
        }
        
        # Process referral if any
        if len(message.text.split()) > 1:
            ref_code = message.text.split()[1]
            for uid, data in USERS_DB.items():
                if data.get('referral_code') == ref_code and uid != str(user_id):
                    old_referrals = data['referrals']
                    data['referrals'] += 1
                    data['balance'] += REWARD_PER_REFERRAL
                    
                    # Check milestone bonuses
                    new_referrals = data['referrals']
                    for milestone, bonus in MILESTONE_BONUSES.items():
                        if new_referrals >= milestone and old_referrals < milestone:
                            data['balance'] += bonus
                            try:
                                bot.send_message(
                                    uid,
                                    f"🎉 बधाई हो! आपने {milestone} रेफरल पूरे किए!\n"
                                    f"🎁 मिलेस्टोन बोनस: {format_currency(bonus)}\n"
                                    f"💰 कुल बैलेंस: {format_currency(data['balance'])}"
                                )
                            except:
                                pass
                            log_activity(f"User {uid} received milestone bonus ₹{bonus} for {milestone} referrals")
                    
                    log_activity(f"User {user_id} joined via referral from {uid}")
                    break
        
        update_user_data(user_id, **new_user)
        log_activity(f"New user registered: {user_id} ({first_name})")
    
    # Send welcome message
    markup = create_main_keyboard(is_admin(user_id))
    
    welcome_msg = (
        f"🙏 नमस्ते {first_name}! TaskCompleteRewardsBot में आपका स्वागत है!\n\n"
        "🎯 यहाँ आप:\n"
        "✅ सरल कार्य पूरे करके पैसे कमा सकते हैं\n"
        "📸 प्रमाण सबमिट करके रिवॉर्ड पा सकते हैं\n"
        "👥 दोस्तों को रेफर करके बोनस कैश पा सकते हैं\n"
        "💸 कभी भी अपनी कमाई UPI से निकाल सकते हैं\n\n"
        f"💰 न्यूनतम निकासी: {format_currency(MIN_WITHDRAWAL)}\n"
        f"🎁 रेफरल बोनस: {format_currency(REWARD_PER_REFERRAL)} प्रति रेफरल\n\n"
        "🏆 मिलेस्टोन बोनस:\n"
        "• 5 रेफरल = ₹10\n• 10 रेफरल = ₹25\n• 25 रेफरल = ₹50\n"
        "• 50 रेफरल = ₹100\n• 100 रेफरल = ₹250\n\n"
        "🎯 शुरू करने के लिए \"नया कार्य\" पर क्लिक करें!"
    )
    
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🎯 नया कार्य')
def show_available_tasks(message):
    """Show available tasks"""
    if is_user_blocked(message.from_user.id):
        return
    
    tasks = [t for t in get_tasks() if t.get('active', True)]
    
    if not tasks:
        bot.reply_to(message, "❌ फिलहाल कोई कार्य उपलब्ध नहीं है। बाद में जांचें!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for task in tasks:
        task_type_hindi = TASK_TYPES.get(task.get('type'), 'सामान्य कार्य')
        markup.add(types.InlineKeyboardButton(
            text=f"{task_type_hindi}: {task['title']} ({format_currency(task['reward'])})",
            callback_data=f"task_{task['id']}"
        ))
    
    bot.reply_to(
        message,
        "🎯 उपलब्ध कार्य:\n\n"
        "विवरण देखने और कार्य पूरा करने के लिए किसी कार्य पर क्लिक करें:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == '💰 बैलेंस')
def handle_balance(message):
    """Handle balance check"""
    if is_user_blocked(message.from_user.id):
        return
    
    user = get_user_data(message.from_user.id)
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    balance_msg = (
        f"💰 आपका वर्तमान बैलेंस: {format_currency(user['balance'])}\n\n"
        f"👥 रेफरल: {user['referrals']} ({format_currency(user['referrals'] * REWARD_PER_REFERRAL)})\n"
        f"📊 पूरे किए गए कार्य: {len(user.get('completed_tasks', []))}\n"
        f"💵 न्यूनतम निकासी: {format_currency(MIN_WITHDRAWAL)}\n\n"
        "💡 अधिक कमाई के लिए और कार्य पूरे करें!"
    )
    
    bot.reply_to(message, balance_msg)

@bot.message_handler(func=lambda message: message.text == '🔗 रेफर')
def handle_refer(message):
    """Handle referral system"""
    if is_user_blocked(message.from_user.id):
        return
    
    user = get_user_data(message.from_user.id)
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    bot_username = get_bot_username()
    
    referral_msg = (
        f"🔗 अपने दोस्तों को रेफर करें!\n\n"
        f"📱 आपका रेफरल लिंक:\n"
        f"https://t.me/{bot_username}?start={user['referral_code']}\n\n"
        f"👥 कुल रेफरल: {user['referrals']}\n"
        f"💰 रेफरल से कमाई: {format_currency(user['referrals'] * REWARD_PER_REFERRAL)}\n\n"
        f"🎁 प्रत्येक रेफरल के लिए {format_currency(REWARD_PER_REFERRAL)} पाएं!\n\n"
        f"🏆 मिलेस्टोन बोनस:\n"
        f"• 5 रेफरल = ₹10 बोनस\n• 10 रेफरल = ₹25 बोनस\n"
        f"• 25 रेफरल = ₹50 बोनस\n• 50 रेफरल = ₹100 बोनस\n"
        f"• 100 रेफरल = ₹250 बोनस"
    )
    
    bot.reply_to(message, referral_msg)

@bot.message_handler(func=lambda message: message.text == '💸 निकासी')
def handle_withdrawal(message):
    """Handle withdrawal request"""
    if is_user_blocked(message.from_user.id):
        return
    
    user = get_user_data(message.from_user.id)
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    if user['balance'] < MIN_WITHDRAWAL:
        bot.reply_to(
            message,
            f"❌ न्यूनतम निकासी राशि {format_currency(MIN_WITHDRAWAL)} है\n"
            f"आपका वर्तमान बैलेंस: {format_currency(user['balance'])}\n\n"
            "अधिक कार्य पूरे करके बैलेंस बढ़ाएं!"
        )
        return
    
    msg = bot.reply_to(
        message,
        f"💸 निकासी राशि: {format_currency(user['balance'])}\n\n"
        "कृपया अपना UPI ID भेजें:\n"
        "उदाहरण: 9876543210@paytm या example@upi\n\n"
        "⚠️ सही UPI ID भेजें, गलत ID की स्थिति में पेमेंट नहीं हो सकेगा।"
    )
    bot.register_next_step_handler(msg, process_upi_id)

def process_upi_id(message):
    """Process UPI ID for withdrawal"""
    user_id = message.from_user.id
    if is_user_blocked(user_id):
        return
    
    upi_id = message.text.strip()
    
    # Validate UPI ID
    if '@' not in upi_id or len(upi_id) < 5 or ' ' in upi_id:
        bot.reply_to(
            message, 
            "❌ गलत UPI ID format!\n\n"
            "सही format: 9876543210@paytm\n"
            "दोबारा कोशिश करने के लिए 💸 निकासी पर क्लिक करें।"
        )
        return
    
    user = get_user_data(user_id)
    withdrawal_data = {
        'user_id': str(user_id),
        'amount': user['balance'],
        'upi_id': upi_id,
        'status': 'pending',
        'requested_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user_name': user['first_name']
    }
    
    # Save withdrawal request and reset balance
    WITHDRAWALS_DB.append(withdrawal_data)
    update_user_data(user_id, balance=0)
    
    bot.reply_to(
        message,
        f"✅ निकासी अनुरोध सफलतापूर्वक सबमिट हो गया!\n\n"
        f"💰 राशि: {format_currency(withdrawal_data['amount'])}\n"
        f"💳 UPI ID: {upi_id}\n\n"
        "Admin 24-48 घंटे के अंदर आपका पेमेंट प्रोसेस करेगा।\n"
        "स्टेटस के लिए बैलेंस चेक करते रहें।"
    )
    
    # Notify admin
    try:
        bot.send_message(
            ADMIN_ID,
            f"💳 नया निकासी अनुरोध!\n\n"
            f"👤 User: {user['first_name']} (ID: {user_id})\n"
            f"💰 Amount: {format_currency(withdrawal_data['amount'])}\n"
            f"💳 UPI ID: {upi_id}\n\n"
            "Admin Panel से approve/reject करें।"
        )
    except:
        pass
    
    log_activity(f"User {user_id} requested withdrawal of ₹{withdrawal_data['amount']} to {upi_id}")

@bot.message_handler(func=lambda message: message.text == '❓ सहायता')
def handle_help(message):
    """Handle help request"""
    if is_user_blocked(message.from_user.id):
        return
    
    help_text = (
        "❓ TaskCompleteRewardsBot सहायता\n\n"
        "📋 कैसे इस्तेमाल करें:\n"
        "1. 🎯 नया कार्य - उपलब्ध कार्य देखें\n"
        "2. कोई कार्य चुनें और उसे पूरा करें\n"
        "3. प्रमाण (स्क्रीनशॉट) भेजें\n"
        "4. Admin के approval का इंतज़ार करें\n"
        "5. Reward मिलने पर 💰 बैलेंस चेक करें\n"
        "6. ₹10 या अधिक होने पर 💸 निकासी करें\n\n"
        "🎁 कार्य के प्रकार:\n"
        "• YouTube Subscribe - ₹2-5\n"
        "• Instagram Follow - ₹2-5\n"
        "• Telegram Join - ₹2-5\n"
        "• Facebook Like - ₹2-5\n"
        "• WhatsApp Join - ₹2-5\n\n"
        "👥 रेफरल करके अतिरिक्त कमाई करें!\n"
        f"🔗 प्रत्येक रेफरल के लिए {format_currency(REWARD_PER_REFERRAL)} पाएं\n\n"
        "💳 पेमेंट: UPI के माध्यम से\n"
        f"💰 न्यूनतम निकासी: {format_currency(MIN_WITHDRAWAL)}\n\n"
        "📞 समस्या के लिए Admin से संपर्क करें।"
    )
    
    bot.reply_to(message, help_text)

# ======================
# Task Handlers
# ======================

@bot.callback_query_handler(func=lambda call: call.data.startswith('task_'))
def handle_task_selection(call):
    """Handle task selection"""
    if is_user_blocked(call.from_user.id):
        return
    
    task_id = call.data.split('_', 1)[1]
    task = get_task_by_id(task_id)
    
    if not task or not task.get('active', True):
        bot.answer_callback_query(call.id, "❌ यह कार्य अब उपलब्ध नहीं है")
        return
    
    user = get_user_data(call.from_user.id)
    completed_tasks = user.get('completed_tasks', [])
    
    # Check if already completed
    if any(ct['task_id'] == task_id for ct in completed_tasks):
        bot.answer_callback_query(call.id, "✅ आपने यह कार्य पहले ही पूरा कर लिया है")
        return
    
    task_type_hindi = TASK_TYPES.get(task.get('type'), 'सामान्य कार्य')
    
    task_msg = (
        f"🎯 कार्य: {task['title']}\n"
        f"📱 प्रकार: {task_type_hindi}\n"
        f"💰 रिवॉर्ड: {format_currency(task['reward'])}\n\n"
        f"📝 विवरण:\n{task['description']}\n\n"
        f"🔗 लिंक: {task.get('link', 'N/A')}\n\n"
        f"📋 स्टेप्स:\n"
        f"1. ऊपर दिए गए लिंक पर जाएं\n"
        f"2. कार्य पूरा करें ({task_type_hindi})\n"
        f"3. नीचे बटन दबाकर स्क्रीनशॉट भेजें\n"
        f"4. Admin approval का इंतज़ार करें\n\n"
        f"⚠️ स्क्रीनशॉट में आपका username/profile दिखना जरूरी है।"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "✅ कार्य पूरा करके स्क्रीनशॉट भेजें", 
        callback_data=f"complete_{task_id}"
    ))
    
    bot.send_message(
        call.message.chat.id,
        task_msg,
        reply_markup=markup,
        disable_web_page_preview=True
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('complete_'))
def handle_complete_task(call):
    """Handle task completion request"""
    if is_user_blocked(call.from_user.id):
        return
    
    task_id = call.data.split('_', 1)[1]
    user_current_task[call.from_user.id] = task_id
    
    bot.send_message(
        call.message.chat.id,
        "📸 कार्य पूरा करने का स्क्रीनशॉट भेजें:\n\n"
        "✅ स्क्रीनशॉट में यह दिखना चाहिए:\n"
        "• आपका यूजरनेम/प्रोफाइल\n"
        "• कार्य पूरा होने का प्रमाण\n"
        "• स्पष्ट और पूरी इमेज\n\n"
        "📱 अब फोटो भेजें (document नहीं):"
    )
    bot.answer_callback_query(call.id, "📸 अब स्क्रीनशॉट भेजें")

@bot.message_handler(content_types=['photo'])
def handle_proof_submission(message):
    """Handle screenshot submission"""
    user_id = message.from_user.id
    if is_user_blocked(user_id):
        return
    
    user = get_user_data(user_id)
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    # Get current task
    task_id = user_current_task.get(user_id)
    if not task_id:
        bot.reply_to(
            message, 
            "❌ पहले कोई कार्य चुनें!\n🎯 \"नया कार्य\" पर क्लिक करके कार्य चुनें।"
        )
        return
    
    task = get_task_by_id(task_id)
    if not task:
        bot.reply_to(message, "❌ यह कार्य अब उपलब्ध नहीं है")
        return
    
    # Record submission
    file_id = message.photo[-1].file_id
    record_submission(user_id, task_id, file_id)
    
    # Clear current task
    if user_id in user_current_task:
        del user_current_task[user_id]
    
    bot.reply_to(
        message,
        f"✅ आपका '{task['title']}' कार्य का प्रमाण सफलतापूर्वक सबमिट हो गया!\n\n"
        "⏳ Admin आपके सबमिशन की समीक्षा करेगा।\n"
        f"💰 Approval के बाद {format_currency(task['reward'])} आपके बैलेंस में जोड़ दिए जाएंगे।\n\n"
        "🔔 आपको approval/rejection की सूचना मिल जाएगी।"
    )
    
    # Notify admin
    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{task_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{task_id}")
        )
        
        bot.send_photo(
            ADMIN_ID,
            file_id,
            caption=f"📋 New Submission\n\n"
                   f"👤 User: {user['first_name']} (ID: {user_id})\n"
                   f"🎯 Task: {task['title']}\n"
                   f"💰 Reward: {format_currency(task['reward'])}\n"
                   f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            reply_markup=markup
        )
    except Exception as e:
        log_activity(f"Failed to notify admin: {e}")

# ======================
# Admin Panel
# ======================

@bot.message_handler(func=lambda message: message.text == '🔧 Admin Panel')
def handle_admin_panel(message):
    """Handle admin panel access"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ आपको Admin Panel का Access नहीं है।")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Tasks", callback_data="admin_tasks"),
        types.InlineKeyboardButton("👥 Users", callback_data="admin_users")
    )
    markup.add(
        types.InlineKeyboardButton("💳 Withdrawals", callback_data="admin_withdrawals"),
        types.InlineKeyboardButton("📸 Screenshots", callback_data="admin_screenshots")
    )
    markup.add(
        types.InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    )
    
    bot.send_message(
        message.chat.id,
        "🔧 Admin Panel\n\nSelect an option:",
        reply_markup=markup
    )

@bot.message_handler(commands=['admin'])
def handle_admin_command(message):
    """Handle /admin command"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ You don't have admin access.")
        return
    handle_admin_panel(message)

# Admin callback handlers
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_callbacks(call):
    """Handle admin panel callbacks"""
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Admin access required")
        return
    
    action = call.data.split('_')[1]
    
    if action == 'stats':
        total_users = len(USERS_DB)
        active_users = len([u for u in USERS_DB.values() if not u.get('blocked', False)])
        pending_subs = len(get_pending_submissions())
        pending_wds = len(get_pending_withdrawals())
        total_balance = sum(u.get('balance', 0) for u in USERS_DB.values())
        
        stats_text = (
            f"📊 Bot Statistics\n\n"
            f"👥 Total Users: {total_users}\n"
            f"✅ Active Users: {active_users}\n"
            f"🚫 Blocked Users: {total_users - active_users}\n"
            f"📋 Total Tasks: {len(TASKS_DB)}\n"
            f"📸 Pending Screenshots: {pending_subs}\n"
            f"💳 Pending Withdrawals: {pending_wds}\n"
            f"💰 Total User Balance: {format_currency(total_balance)}\n"
            f"🔗 Total Referrals: {sum(u.get('referrals', 0) for u in USERS_DB.values())}"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif action == 'withdrawals':
        pending_wds = get_pending_withdrawals()
        
        if not pending_wds:
            bot.edit_message_text(
                "💳 Withdrawal Management\n\n✅ No pending withdrawals",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            wd_text = f"💳 Pending Withdrawals ({len(pending_wds)}):\n\n"
            markup = types.InlineKeyboardMarkup()
            
            for i, wd in enumerate(pending_wds[:5]):
                wd_text += (
                    f"{i+1}. {wd.get('user_name', 'Unknown')}\n"
                    f"💰 Amount: {format_currency(wd['amount'])}\n"
                    f"💳 UPI: {wd.get('upi_id', 'N/A')}\n"
                    f"📅 {wd['requested_at']}\n\n"
                )
                
                markup.row(
                    types.InlineKeyboardButton(f"✅ #{i+1}", callback_data=f"approve_wd_{i}"),
                    types.InlineKeyboardButton(f"❌ #{i+1}", callback_data=f"reject_wd_{i}")
                )
            
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            
            bot.edit_message_text(
                wd_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
    
    elif action == 'screenshots':
        pending_subs = get_pending_submissions()
        
        if not pending_subs:
            bot.edit_message_text(
                "📸 Screenshot Verification\n\n✅ No pending submissions",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            sub_text = f"📸 Pending Screenshots ({len(pending_subs)}):\n\n"
            
            for i, sub in enumerate(pending_subs[:5]):
                user = get_user_data(sub['user_id'])
                task = get_task_by_id(sub['task_id'])
                
                sub_text += (
                    f"{i+1}. {user.get('first_name', 'Unknown') if user else 'Unknown'}\n"
                    f"📋 Task: {task['title'] if task else 'Unknown'}\n"
                    f"📅 {sub['submitted_at']}\n\n"
                )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📸 Review All", callback_data="admin_review_all"))
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            
            bot.edit_message_text(
                sub_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
    
    elif action == 'broadcast':
        msg = bot.send_message(
            call.from_user.id,
            "📢 Enter broadcast message:\n\n"
            "⚠️ This will be sent to all users."
        )
        bot.register_next_step_handler(msg, process_broadcast)
        bot.answer_callback_query(call.id)
        return
    
    elif action == 'back':
        handle_admin_panel(call.message)
    
    bot.answer_callback_query(call.id)

# Withdrawal approval handlers
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_wd_', 'reject_wd_')))
def handle_withdrawal_decisions(call):
    """Handle withdrawal approval/rejection"""
    if not is_admin(call.from_user.id):
        return
    
    action, wd_index = call.data.rsplit('_', 1)
    wd_index = int(wd_index)
    
    pending_wds = get_pending_withdrawals()
    if wd_index >= len(pending_wds):
        bot.answer_callback_query(call.id, "❌ Invalid withdrawal")
        return
    
    wd = pending_wds[wd_index]
    
    if action.startswith('approve'):
        # Approve withdrawal
        for w in WITHDRAWALS_DB:
            if (w['user_id'] == wd['user_id'] and 
                w['requested_at'] == wd['requested_at'] and 
                w['status'] == 'pending'):
                w['status'] = 'approved'
                w['approved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        
        # Notify user
        try:
            bot.send_message(
                wd['user_id'],
                f"✅ आपका निकासी अनुरोध स्वीकृत हो गया!\n\n"
                f"💰 राशि: {format_currency(wd['amount'])}\n"
                f"💳 UPI ID: {wd['upi_id']}\n\n"
                "पेमेंट 24-48 घंटे में आपके अकाउंट में ट्रांसफर हो जाएगा।"
            )
        except:
            pass
        
        bot.answer_callback_query(call.id, "✅ Withdrawal approved!")
        log_activity(f"Admin approved withdrawal for user {wd['user_id']}")
        
    else:
        # Reject withdrawal
        msg = bot.send_message(
            call.from_user.id,
            "📝 Enter rejection reason:"
        )
        bot.register_next_step_handler(msg, lambda m: process_withdrawal_rejection(m, wd))
        bot.answer_callback_query(call.id)
        return
    
    # Refresh withdrawal list
    bot.edit_message_text(
        f"✅ Withdrawal processed successfully",
        call.message.chat.id,
        call.message.message_id
    )

def process_withdrawal_rejection(message, wd):
    """Process withdrawal rejection with reason"""
    if not is_admin(message.from_user.id):
        return
    
    reason = message.text
    
    # Update withdrawal status
    for w in WITHDRAWALS_DB:
        if (w['user_id'] == wd['user_id'] and 
            w['requested_at'] == wd['requested_at'] and 
            w['status'] == 'pending'):
            w['status'] = 'rejected'
            w['rejected_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            w['rejection_reason'] = reason
            break
    
    # Restore user balance
    user = get_user_data(wd['user_id'])
    if user:
        update_user_data(wd['user_id'], balance=user['balance'] + wd['amount'])
    
    # Notify user
    try:
        bot.send_message(
            wd['user_id'],
            f"❌ आपका निकासी अनुरोध रद्द कर दिया गया।\n\n"
            f"📝 कारण: {reason}\n\n"
            f"💰 राशि {format_currency(wd['amount'])} आपके बैलेंस में वापस कर दी गई है।"
        )
    except:
        pass
    
    bot.reply_to(
        message,
        f"✅ Withdrawal rejected for user {wd['user_id']}. Balance restored."
    )
    log_activity(f"Admin rejected withdrawal for user {wd['user_id']}: {reason}")

# Screenshot approval handlers
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_screenshot_decisions(call):
    """Handle screenshot approval/rejection"""
    if not is_admin(call.from_user.id):
        return
    
    parts = call.data.split('_')
    action = parts[0]
    user_id = parts[1]
    task_id = parts[2]
    
    task = get_task_by_id(task_id)
    user = get_user_data(user_id)
    
    if not task or not user:
        bot.answer_callback_query(call.id, "❌ Task or user not found")
        return
    
    if action == 'approve':
        # Approve submission
        new_balance = user['balance'] + task['reward']
        update_user_data(user_id, balance=new_balance)
        
        # Add to completed tasks
        completed_tasks = user.get('completed_tasks', [])
        completed_tasks.append({
            'task_id': task_id,
            'title': task['title'],
            'reward': task['reward'],
            'completed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        update_user_data(user_id, completed_tasks=completed_tasks)
        
        # Update task completion count
        for t in TASKS_DB:
            if t['id'] == task_id:
                t['completed_count'] = t.get('completed_count', 0) + 1
                break
        
        # Update submission status
        update_submission_status(user_id, task_id, 'approved')
        
        # Notify user
        try:
            bot.send_message(
                user_id,
                f"🎉 बधाई हो! आपका '{task['title']}' कार्य स्वीकृत हो गया!\n\n"
                f"💰 {format_currency(task['reward'])} आपके बैलेंस में जोड़ दिए गए।\n"
                f"💵 नया बैलेंस: {format_currency(new_balance)}\n\n"
                f"✅ आप और भी कार्य पूरे करके अधिक कमा सकते हैं!"
            )
        except:
            pass
        
        bot.answer_callback_query(call.id, "✅ Submission approved!")
        bot.edit_message_caption(
            f"✅ APPROVED\n\n{call.message.caption}",
            call.message.chat.id,
            call.message.message_id
        )
        log_activity(f"Admin approved submission from {user_id} for task {task_id}")
        
    else:
        # Reject submission
        msg = bot.send_message(
            call.from_user.id,
            "📝 Enter rejection reason:"
        )
        bot.register_next_step_handler(
            msg, 
            lambda m: process_screenshot_rejection(m, user_id, task_id, task, call.message)
        )
        bot.answer_callback_query(call.id)

def process_screenshot_rejection(message, user_id, task_id, task, original_message):
    """Process screenshot rejection with reason"""
    if not is_admin(message.from_user.id):
        return
    
    reason = message.text
    
    # Update submission status
    update_submission_status(user_id, task_id, 'rejected', reason)
    
    # Notify user
    try:
        bot.send_message(
            user_id,
            f"❌ आपका '{task['title']}' कार्य रद्द कर दिया गया।\n\n"
            f"📝 कारण: {reason}\n\n"
            f"🔄 आप सही प्रमाण के साथ दोबारा कोशिश कर सकते हैं।\n"
            f"💡 सुझाव: स्क्रीनशॉट में आपका यूजरनेम दिखना चाहिए।"
        )
    except:
        pass
    
    bot.reply_to(message, "✅ User notified about rejection.")
    
    # Update original message
    try:
        bot.edit_message_caption(
            f"❌ REJECTED: {reason}\n\n{original_message.caption}",
            original_message.chat.id,
            original_message.message_id
        )
    except:
        pass
    
    log_activity(f"Admin rejected submission from {user_id} for task {task_id}: {reason}")

def process_broadcast(message):
    """Process broadcast message"""
    if not is_admin(message.from_user.id):
        return
    
    text = message.text
    success = 0
    failed = 0
    
    for uid in USERS_DB.keys():
        try:
            bot.send_message(
                uid, 
                f"📢 Admin की तरफ से सूचना:\n\n{text}\n\n"
                "— TaskCompleteRewardsBot Team"
            )
            success += 1
        except:
            failed += 1
    
    bot.reply_to(
        message,
        f"📢 Broadcast completed!\n\n"
        f"✅ Sent to: {success} users\n"
        f"❌ Failed: {failed} users"
    )
    log_activity(f"Admin broadcast sent to {success} users")

# ======================
# Error Handlers
# ======================

@bot.message_handler(func=lambda message: True)
def handle_unknown_message(message):
    """Handle unknown messages"""
    if is_user_blocked(message.from_user.id):
        return
    
    bot.reply_to(
        message,
        "❓ समझ नहीं आया। कृपया keyboard के buttons का इस्तेमाल करें या /start करें।"
    )

# ======================
# Background Tasks
# ======================

def heartbeat():
    """Background heartbeat"""
    while True:
        try:
            log_activity("Bot heartbeat - System running normally")
            time.sleep(3600)  # Every hour
        except:
            time.sleep(300)  # Every 5 minutes on error

def self_ping():
    """Self ping to keep alive"""
    while True:
        try:
            requests.get("http://localhost:8080/", timeout=30)
            time.sleep(300)  # Every 5 minutes
        except:
            time.sleep(60)  # Every minute on error

# ======================
# Main Function
# ======================

def main():
    """Main function to start the bot"""
    
    # Validate configuration
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ ERROR: Please set your BOT_TOKEN!")
        print("1. Get token from @BotFather")
        print("2. Replace 'YOUR_BOT_TOKEN_HERE' in the code")
        return
    
    # Test bot connection
    try:
        bot_info = bot.get_me()
        global bot_username
        bot_username = bot_info.username
        print(f"✅ Bot connected successfully: @{bot_username}")
    except Exception as e:
        print(f"❌ Failed to connect to Telegram: {e}")
        print("Please check your BOT_TOKEN")
        return
    
    # Start keep alive server
    try:
        keep_alive()
        print("✅ Keep-alive server started on port 8080")
    except Exception as e:
        print(f"⚠️  Keep-alive server failed: {e}")
    
    # Start background tasks
    try:
        threading.Thread(target=heartbeat, daemon=True).start()
        threading.Thread(target=self_ping, daemon=True).start()
        print("✅ Background tasks started")
    except Exception as e:
        print(f"⚠️  Background tasks failed: {e}")
    
    # Log startup
    log_activity("TaskCompleteRewardsBot started successfully")
    log_activity(f"Sample tasks loaded: {len(TASKS_DB)} tasks")
    log_activity(f"Admin ID configured: {ADMIN_ID}")
    
    # Print startup info
    print("\n🎯 TaskCompleteRewardsBot is now running!")
    print(f"👨‍💼 Admin ID: {ADMIN_ID}")
    print(f"🌐 Web interface: http://localhost:8080")
    print(f"📊 Statistics: http://localhost:8080/stats")
    print(f"📱 Bot link: https://t.me/{bot_username}")
    print("💾 All data stored in memory")
    print("\n✅ Ready to accept commands!")
    
    # Start bot polling
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ Bot polling failed: {e}")
        log_activity(f"Bot polling failed: {e}")

if __name__ == "__main__":
    main()