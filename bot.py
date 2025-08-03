import os
import json
import threading
import time
import random
import string
import requests
from datetime import datetime
from flask import Flask
import telebot
from telebot import types

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '7599681001:AAGLez6NxGQ3VsE8itJ1E0U73r8ZtUYvZkc')
ADMIN_ID = 5367009004  # Admin ID as specified
MIN_WITHDRAWAL = 10  # ₹10 minimum withdrawal
REWARD_PER_REFERRAL = 2  # ₹2 per referral
MAX_TASKS_PER_USER = 10  # Increased limit
DAILY_TASK_LIMIT = 20  # Increased limit

# Milestone bonuses for referrals
MILESTONE_BONUSES = {
    5: 10,    # ₹10 for 5 referrals
    10: 25,   # ₹25 for 10 referrals
    25: 50,   # ₹50 for 25 referrals
    50: 100,  # ₹100 for 50 referrals
    100: 250  # ₹250 for 100 referrals
}

# Task types
TASK_TYPES = {
    'youtube_subscribe': 'YouTube Subscribe',
    'instagram_follow': 'Instagram Follow', 
    'telegram_join': 'Telegram Join',
    'facebook_like': 'Facebook Like',
    'whatsapp_join': 'WhatsApp Join'
}

# File paths
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
SUBMISSIONS_FILE = os.path.join(DATA_DIR, "submissions.json")
WITHDRAWALS_FILE = os.path.join(DATA_DIR, "withdrawals.json")
LOG_FILE = os.path.join(DATA_DIR, "logs.json")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)
blocked_users = set()

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ======================
# Database Functions
# ======================

def initialize_data_files():
    for file_path in [USERS_FILE, TASKS_FILE, SUBMISSIONS_FILE, WITHDRAWALS_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                if file_path == TASKS_FILE:
                    json.dump([], f)
                elif file_path == SUBMISSIONS_FILE:
                    json.dump({}, f)
                elif file_path == WITHDRAWALS_FILE:
                    json.dump([], f)
                else:
                    json.dump({}, f)

def get_user_data(user_id):
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            return users.get(str(user_id))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def update_user_data(user_id, data=None, field=None, value=None):
    try:
        with open(USERS_FILE, 'r+') as f:
            users = json.load(f)
            
            if data:
                users[str(user_id)] = data
            elif field:
                if str(user_id) not in users:
                    users[str(user_id)] = {}
                users[str(user_id)][field] = value
            
            f.seek(0)
            json.dump(users, f)
            f.truncate()
            return True
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def get_tasks():
    try:
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def add_task(task):
    try:
        with open(TASKS_FILE, 'r+') as f:
            tasks = json.load(f)
            tasks.append(task)
            f.seek(0)
            json.dump(tasks, f)
            f.truncate()
            return True
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def record_submission(user_id, task_id, file_id):
    try:
        with open(SUBMISSIONS_FILE, 'r+') as f:
            submissions = json.load(f)
            
            if str(user_id) not in submissions:
                submissions[str(user_id)] = []
            
            submissions[str(user_id)].append({
                'task_id': task_id,
                'file_id': file_id,
                'status': 'pending',
                'submitted_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            f.seek(0)
            json.dump(submissions, f)
            f.truncate()
            return True
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def get_pending_submissions():
    try:
        with open(SUBMISSIONS_FILE, 'r') as f:
            submissions = json.load(f)
            pending = []
            
            for user_id, user_submissions in submissions.items():
                for sub in user_submissions:
                    if sub['status'] == 'pending':
                        pending.append({
                            'user_id': user_id,
                            'task_id': sub['task_id'],
                            'file_id': sub['file_id'],
                            'submitted_at': sub['submitted_at']
                        })
            
            return pending
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def update_submission_status(user_id, task_id, status, reason=None):
    try:
        with open(SUBMISSIONS_FILE, 'r+') as f:
            submissions = json.load(f)
            
            if str(user_id) not in submissions:
                return False
            
            for sub in submissions[str(user_id)]:
                if sub['task_id'] == task_id and sub['status'] == 'pending':
                    sub['status'] = status
                    sub['processed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if reason:
                        sub['reason'] = reason
                    break
            
            f.seek(0)
            json.dump(submissions, f)
            f.truncate()
            return True
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def request_withdrawal(user_id, amount, method):
    try:
        with open(WITHDRAWALS_FILE, 'r+') as f:
            withdrawals = json.load(f)
            
            withdrawals.append({
                'user_id': str(user_id),
                'amount': amount,
                'method': method,
                'status': 'pending',
                'requested_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            f.seek(0)
            json.dump(withdrawals, f)
            f.truncate()
            return True
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def get_pending_withdrawals():
    try:
        with open(WITHDRAWALS_FILE, 'r') as f:
            withdrawals = json.load(f)
            return [w for w in withdrawals if w['status'] == 'pending']
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def update_withdrawal_status(user_id, requested_at, status):
    try:
        with open(WITHDRAWALS_FILE, 'r+') as f:
            withdrawals = json.load(f)
            
            for w in withdrawals:
                if w['user_id'] == str(user_id) and w['requested_at'] == requested_at:
                    w['status'] = status
                    w['processed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            
            f.seek(0)
            json.dump(withdrawals, f)
            f.truncate()
            return True
    except (FileNotFoundError, json.JSONDecodeError):
        return False

# ======================
# Utility Functions
# ======================

def log_activity(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "message": message
    }
    
    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    logs.append(log_entry)
    
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)
    
    print(f"[{timestamp}] {message}")

def generate_referral_code(user_id):
    return f"REF-{user_id}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def is_admin(user_id):
    return int(user_id) == ADMIN_ID

def is_user_blocked(user_id):
    return str(user_id) in blocked_users

def block_user(user_id):
    blocked_users.add(str(user_id))
    update_user_data(user_id, 'blocked', True)
    log_activity(f"User {user_id} blocked by system")

# ======================
# Keep Alive Server
# ======================

app = Flask(__name__)

@app.route('/')
def home():
    return "TaskRewardBot is running!"

@app.route('/ping')
def ping():
    return "pong"

@app.route('/status')
def status():
    return "Bot is alive!"

@app.route('/alive')
def alive():
    return "OK"

def keep_alive():
    server = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    server.daemon = True
    server.start()

# ======================
# Background Tasks
# ======================

def self_ping_loop():
    while True:
        try:
            requests.get("http://localhost:8080/ping")
            time.sleep(120)
        except Exception as e:
            log_activity(f"Ping error: {str(e)}")
            time.sleep(60)

def heartbeat_loop():
    while True:
        log_activity("Heartbeat check - Bot is running")
        time.sleep(3600)

# ======================
# User Handlers
# ======================

@bot.message_handler(commands=['start'])
def handle_start(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    
    user = get_user_data(user_id)
    
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
        
        if len(message.text.split()) > 1:
            ref_code = message.text.split()[1]
            with open(USERS_FILE, 'r+') as f:
                users = json.load(f)
                for uid, data in users.items():
                    if data.get('referral_code') == ref_code:
                        old_referrals = data['referrals']
                        data['referrals'] += 1
                        data['balance'] += REWARD_PER_REFERRAL
                        
                        # Check for milestone bonuses
                        new_referrals = data['referrals']
                        for milestone, bonus in MILESTONE_BONUSES.items():
                            if new_referrals >= milestone and old_referrals < milestone:
                                data['balance'] += bonus
                                bot.send_message(
                                    uid,
                                    f"🎉 बधाई हो! आपने {milestone} रेफरल पूरे किए!\n"
                                    f"🎁 मिलेस्टोन बोनस: ₹{bonus}\n"
                                    f"💰 कुल बैलेंस: ₹{data['balance']}"
                                )
                                log_activity(f"User {uid} received milestone bonus ₹{bonus} for {milestone} referrals")
                        
                        f.seek(0)
                        json.dump(users, f)
                        f.truncate()
                        log_activity(f"User {user_id} joined via referral from {uid}")
                        break
        
        update_user_data(user_id, new_user)
        log_activity(f"New user registered: {user_id}")
    
    # Check if user is admin to show admin panel
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if is_admin(user_id):
        markup.add(types.KeyboardButton('🎯 नया कार्य'), types.KeyboardButton('🔧 Admin Panel'))
        markup.add(types.KeyboardButton('💰 बैलेंस'), types.KeyboardButton('🔗 रेफर'))
        markup.add(types.KeyboardButton('💸 निकासी'), types.KeyboardButton('❓ सहायता'))
    else:
        markup.add(types.KeyboardButton('🎯 नया कार्य'))
        markup.add(types.KeyboardButton('💰 बैलेंस'), types.KeyboardButton('🔗 रेफर'))
        markup.add(types.KeyboardButton('💸 निकासी'), types.KeyboardButton('❓ सहायता'))
    
    welcome_msg = (
        f"🙏 नमस्ते {first_name}! TaskCompleteRewardsBot में आपका स्वागत है!\n\n"
        "✅ सरल कार्य पूरे करके पैसे कमाएं\n"
        "📸 प्रमाण सबमिट करके रिवॉर्ड पाएं\n"
        "👥 दोस्तों को रेफर करके बोनस कैश पाएं\n"
        "💸 कभी भी अपनी कमाई निकालें\n\n"
        f"💰 न्यूनतम निकासी: ₹{MIN_WITHDRAWAL}\n"
        f"🎁 रेफरल बोनस: ₹{REWARD_PER_REFERRAL} प्रति रेफरल\n\n"
        "🏆 मिलेस्टोन बोनस:\n"
        "• 5 रेफरल = ₹10\n"
        "• 10 रेफरल = ₹25\n"
        "• 25 रेफरल = ₹50\n"
        "• 50 रेफरल = ₹100\n"
        "• 100 रेफरल = ₹250"
    )
    
    bot.send_message(chat_id, welcome_msg, reply_markup=markup)

@bot.message_handler(commands=['balance'])
def handle_balance(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    bot.reply_to(
        message,
        f"💰 आपका वर्तमान बैलेंस: ₹{user['balance']}\n\n"
        f"👥 रेफरल: {user['referrals']} (₹{user['referrals'] * REWARD_PER_REFERRAL})\n"
        f"💵 न्यूनतम निकासी: ₹{MIN_WITHDRAWAL}\n"
        f"📊 पूरे किए गए कार्य: {len(user.get('completed_tasks', []))}"
    )

@bot.message_handler(commands=['refer'])
def handle_refer(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    # Get bot username dynamically
    bot_info = bot.get_me()
    bot_username = bot_info.username
    
    referral_msg = (
        f"🔗 अपने दोस्तों को रेफर करें और प्रत्येक के लिए ₹{REWARD_PER_REFERRAL} कमाएं!\n\n"
        f"📱 आपका रेफरल लिंक:\n"
        f"https://t.me/{bot_username}?start={user['referral_code']}\n\n"
        f"👥 कुल रेफरल: {user['referrals']}\n"
        f"💰 रेफरल से कमाई: ₹{user['referrals'] * REWARD_PER_REFERRAL}\n\n"
        f"🏆 मिलेस्टोन बोनस:\n"
        f"• 5 रेफरल = ₹10 बोनस\n"
        f"• 10 रेफरल = ₹25 बोनस\n"
        f"• 25 रेफरल = ₹50 बोनस\n"
        f"• 50 रेफरल = ₹100 बोनस\n"
        f"• 100 रेफरल = ₹250 बोनस"
    )
    
    bot.reply_to(message, referral_msg)

@bot.message_handler(commands=['withdrawal'])
def handle_withdrawal(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    if user['balance'] < MIN_WITHDRAWAL:
        bot.reply_to(
            message,
            f"❌ न्यूनतम निकासी राशि ₹{MIN_WITHDRAWAL} है\n"
            f"आपका वर्तमान बैलेंस: ₹{user['balance']}"
        )
        return
    
    msg = bot.reply_to(
        message,
        f"💸 निकासी राशि: ₹{user['balance']}\n\n"
        "कृपया अपना UPI ID भेजें (जैसे: 9876543210@paytm):"
    )
    bot.register_next_step_handler(msg, process_upi_id)

def process_upi_id(message):
    user_id = message.from_user.id
    if is_user_blocked(user_id):
        return
    
    upi_id = message.text.strip()
    
    # Basic UPI ID validation
    if '@' not in upi_id or len(upi_id) < 5:
        bot.reply_to(message, "❌ कृपया सही UPI ID भेजें (जैसे: 9876543210@paytm)")
        return
    
    user = get_user_data(user_id)
    withdrawal_data = {
        'user_id': str(user_id),
        'amount': user['balance'],
        'upi_id': upi_id,
        'status': 'pending',
        'requested_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save withdrawal request
    try:
        with open(WITHDRAWALS_FILE, 'r+') as f:
            withdrawals = json.load(f)
            withdrawals.append(withdrawal_data)
            f.seek(0)
            json.dump(withdrawals, f)
            f.truncate()
    except (FileNotFoundError, json.JSONDecodeError):
        with open(WITHDRAWALS_FILE, 'w') as f:
            json.dump([withdrawal_data], f)
    
    # Reset user balance to 0
    update_user_data(user_id, field='balance', value=0)
    
    bot.reply_to(
        message,
        f"✅ निकासी अनुरोध सबमिट हो गया!\n\n"
        f"💰 राशि: ₹{withdrawal_data['amount']}\n"
        f"💳 UPI ID: {upi_id}\n\n"
        "Admin 24 घंटे के अंदर आपका पेमेंट प्रोसेस करेगा।"
    )
    log_activity(f"User {user_id} requested ₹{withdrawal_data['amount']} withdrawal to UPI {upi_id}")

# Keep the old function for compatibility but rename it
def process_withdrawal_method(message):
    # This is for backward compatibility - redirect to UPI processing
    process_upi_id(message)

@bot.message_handler(commands=['help'])
def handle_help(message):
    if is_user_blocked(message.from_user.id):
        return
    
    help_text = (
        "❓ TaskCompleteRewardsBot सहायता\n\n"
        "📋 उपलब्ध कमांड:\n"
        "/start - बॉट शुरू करें और रजिस्टर करें\n"
        "/balance - अपनी कमाई देखें\n"
        "/refer - अपना रेफरल लिंक पाएं\n"
        "/withdrawal - पैसे निकालने का अनुरोध करें\n"
        "/help - यह सहायता संदेश दिखाएं\n\n"
        "📌 यह कैसे काम करता है:\n"
        "1. 🎯 नया कार्य से उपलब्ध कार्य देखें\n"
        "2. कोई कार्य पूरा करें\n"
        "3. प्रमाण (स्क्रीनशॉट) सबमिट करें\n"
        "4. अप्रूवल के बाद रिवॉर्ड पाएं\n"
        "5. अपनी कमाई निकालें\n\n"
        "🎁 कार्य प्रकार:\n"
        "• YouTube Subscribe - ₹2-5\n"
        "• Instagram Follow - ₹2-5\n"
        "• Telegram Join - ₹2-5\n"
        "• Facebook Like - ₹2-5\n"
        "• WhatsApp Join - ₹2-5\n\n"
        "👥 दोस्तों को रेफर करके अतिरिक्त पैसे कमाएं!\n"
        f"💰 न्यूनतम निकासी: ₹{MIN_WITHDRAWAL}\n"
        f"🔗 रेफरल बोनस: ₹{REWARD_PER_REFERRAL} प्रति रेफरल"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: message.text == '🎯 नया कार्य')
def show_available_tasks(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    tasks = get_tasks()
    
    if not tasks:
        bot.reply_to(message, "❌ फिलहाल कोई कार्य उपलब्ध नहीं है। बाद में जांचें!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for task in tasks:
        if task.get('active', True):
            task_type_hindi = TASK_TYPES.get(task.get('type', 'general'), task.get('type', 'सामान्य'))
            markup.add(types.InlineKeyboardButton(
                text=f"{task_type_hindi}: {task['title']} (₹{task['reward']})",
                callback_data=f"task_{task['id']}"
            ))
    
    bot.reply_to(
        message,
        "🎯 उपलब्ध कार्य\n\n"
        "विवरण देखने और कार्य पूरा करने के लिए किसी कार्य पर क्लिक करें:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == '💰 बैलेंस')
def handle_balance_button(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    bot.reply_to(
        message,
        f"💰 आपका वर्तमान बैलेंस: ₹{user['balance']}\n\n"
        f"👥 रेफरल: {user['referrals']} (₹{user['referrals'] * REWARD_PER_REFERRAL})\n"
        f"💵 न्यूनतम निकासी: ₹{MIN_WITHDRAWAL}\n"
        f"📊 पूरे किए गए कार्य: {len(user.get('completed_tasks', []))}"
    )

@bot.message_handler(func=lambda message: message.text == '🔗 रेफर')
def handle_refer_button(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    # Get bot username dynamically
    try:
        bot_info = bot.get_me()
        bot_username = bot_info.username
    except:
        bot_username = "YourBotUsername"  # Fallback
    
    referral_msg = (
        f"🔗 अपने दोस्तों को रेफर करें और प्रत्येक के लिए ₹{REWARD_PER_REFERRAL} कमाएं!\n\n"
        f"📱 आपका रेफरल लिंक:\n"
        f"https://t.me/{bot_username}?start={user['referral_code']}\n\n"
        f"👥 कुल रेफरल: {user['referrals']}\n"
        f"💰 रेफरल से कमाई: ₹{user['referrals'] * REWARD_PER_REFERRAL}\n\n"
        f"🏆 मिलेस्टोन बोनस:\n"
        f"• 5 रेफरल = ₹10 बोनस\n"
        f"• 10 रेफरल = ₹25 बोनस\n"
        f"• 25 रेफरल = ₹50 बोनस\n"
        f"• 50 रेफरल = ₹100 बोनस\n"
        f"• 100 रेफरल = ₹250 बोनस"
    )
    
    bot.reply_to(message, referral_msg)

@bot.message_handler(func=lambda message: message.text == '💸 निकासी')
def handle_withdraw_button(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    if user['balance'] < MIN_WITHDRAWAL:
        bot.reply_to(
            message,
            f"❌ न्यूनतम निकासी राशि ₹{MIN_WITHDRAWAL} है\n"
            f"आपका वर्तमान बैलेंस: ₹{user['balance']}"
        )
        return
    
    msg = bot.reply_to(
        message,
        f"💸 निकासी राशि: ₹{user['balance']}\n\n"
        "कृपया अपना UPI ID भेजें (जैसे: 9876543210@paytm):"
    )
    bot.register_next_step_handler(msg, process_upi_id)

@bot.message_handler(func=lambda message: message.text == '📊 My Tasks')
def handle_my_tasks_button(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ You need to start the bot first with /start")
        return
    
    # Get user's submissions
    try:
        with open(SUBMISSIONS_FILE, 'r') as f:
            submissions = json.load(f)
            user_submissions = submissions.get(str(user_id), [])
    except (FileNotFoundError, json.JSONDecodeError):
        user_submissions = []
    
    if not user_submissions:
        bot.reply_to(message, "📊 You haven't submitted any tasks yet.")
        return
    
    response = "📊 Your Task History:\n\n"
    for sub in user_submissions[-10:]:  # Show last 10 submissions
        status_emoji = "⏳" if sub['status'] == 'pending' else "✅" if sub['status'] == 'approved' else "❌"
        response += f"{status_emoji} {sub['task_id']} - {sub['status'].title()}\n"
        response += f"📅 {sub['submitted_at']}\n\n"
    
    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: message.text == '❓ सहायता')
def handle_help_button(message):
    if is_user_blocked(message.from_user.id):
        return
    
    help_text = (
        "❓ TaskCompleteRewardsBot सहायता\n\n"
        "📋 उपलब्ध बटन:\n"
        "🎯 नया कार्य - कार्य ब्राउज़ करें और पूरा करें\n"
        "💰 बैलेंस - अपनी कमाई देखें\n"
        "🔗 रेफर - अपना रेफरल लिंक पाएं\n"
        "💸 निकासी - पैसे निकालने का अनुरोध करें\n"
        "❓ सहायता - यह सहायता संदेश दिखाएं\n\n"
        "📌 यह कैसे काम करता है:\n"
        "1. 🎯 नया कार्य से उपलब्ध कार्य देखें\n"
        "2. कोई कार्य पूरा करें\n"
        "3. प्रमाण (स्क्रीनशॉट) सबमिट करें\n"
        "4. अप्रूवल के बाद रिवॉर्ड पाएं\n"
        "5. अपनी कमाई निकालें\n\n"
        "🎁 कार्य प्रकार:\n"
        "• YouTube Subscribe - ₹2-5\n"
        "• Instagram Follow - ₹2-5\n"
        "• Telegram Join - ₹2-5\n"
        "• Facebook Like - ₹2-5\n"
        "• WhatsApp Join - ₹2-5\n\n"
        "👥 दोस्तों को रेफर करके अतिरिक्त पैसे कमाएं!\n"
        f"💰 न्यूनतम निकासी: ₹{MIN_WITHDRAWAL}\n"
        f"🔗 रेफरल बोनस: ₹{REWARD_PER_REFERRAL} प्रति रेफरल\n\n"
        "📞 सहायता के लिए Admin से संपर्क करें"
    )
    bot.reply_to(message, help_text)

# Admin Panel Handler
@bot.message_handler(func=lambda message: message.text == '🔧 Admin Panel')
def handle_admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ आपको Admin Panel का Access नहीं है।")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Manage Tasks", callback_data="admin_tasks"),
        types.InlineKeyboardButton("👥 View Users", callback_data="admin_users")
    )
    markup.add(
        types.InlineKeyboardButton("💳 Withdrawals", callback_data="admin_withdrawals"),
        types.InlineKeyboardButton("📸 Screenshots", callback_data="admin_screenshots")
    )
    markup.add(
        types.InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    )
    markup.add(
        types.InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings"),
        types.InlineKeyboardButton("📝 Logs", callback_data="admin_logs")
    )
    
    bot.send_message(
        message.chat.id,
        "🔧 Admin Panel\n\nSelect an option:",
        reply_markup=markup
    )

@bot.message_handler(commands=['admin'])
def handle_admin_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ You don't have admin access.")
        return
    
    handle_admin_panel(message)

# Admin Callback Handlers
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_callbacks(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Admin access required")
        return
    
    action = call.data.split('_')[1]
    
    if action == 'tasks':
        # Manage Tasks
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ Add Task", callback_data="admin_add_task"),
            types.InlineKeyboardButton("📝 Edit Task", callback_data="admin_edit_task")
        )
        markup.add(
            types.InlineKeyboardButton("🗑️ Delete Task", callback_data="admin_delete_task"),
            types.InlineKeyboardButton("📊 Task Stats", callback_data="admin_task_stats")
        )
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(
            "📋 Task Management\n\nSelect an option:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif action == 'users':
        # View Users with pagination
        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
        except:
            users = {}
        
        total_users = len(users)
        active_users = len([u for u in users.values() if not u.get('blocked', False)])
        
        user_text = f"👥 User Management\n\n"
        user_text += f"📊 Total Users: {total_users}\n"
        user_text += f"✅ Active Users: {active_users}\n"
        user_text += f"❌ Blocked Users: {total_users - active_users}\n\n"
        
        # Show top 5 users by balance
        sorted_users = sorted(users.items(), key=lambda x: x[1].get('balance', 0), reverse=True)
        user_text += "💰 Top Earners:\n"
        for i, (uid, data) in enumerate(sorted_users[:5], 1):
            user_text += f"{i}. {data.get('first_name', 'Unknown')} - ₹{data.get('balance', 0)}\n"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("👥 All Users", callback_data="admin_all_users"),
            types.InlineKeyboardButton("🚫 Block User", callback_data="admin_block_user")
        )
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(
            user_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif action == 'withdrawals':
        # View pending withdrawals
        try:
            with open(WITHDRAWALS_FILE, 'r') as f:
                withdrawals = json.load(f)
            pending_withdrawals = [w for w in withdrawals if w['status'] == 'pending']
        except:
            pending_withdrawals = []
        
        if not pending_withdrawals:
            bot.edit_message_text(
                "💳 Withdrawal Management\n\n✅ No pending withdrawals",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            wd_text = f"💳 Pending Withdrawals ({len(pending_withdrawals)}):\n\n"
            for i, wd in enumerate(pending_withdrawals[:5], 1):
                try:
                    user = get_user_data(wd['user_id'])
                    user_name = user['first_name'] if user else 'Unknown'
                except:
                    user_name = 'Unknown'
                
                wd_text += f"{i}. {user_name}\n"
                wd_text += f"💰 Amount: ₹{wd['amount']}\n"
                wd_text += f"💳 UPI: {wd.get('upi_id', wd.get('method', 'N/A'))}\n"
                wd_text += f"📅 {wd['requested_at']}\n\n"
            
            markup = types.InlineKeyboardMarkup()
            for i, wd in enumerate(pending_withdrawals[:3]):
                markup.add(
                    types.InlineKeyboardButton(
                        f"✅ Approve #{i+1}", 
                        callback_data=f"approve_wd_{wd['user_id']}_{wd['requested_at']}"
                    ),
                    types.InlineKeyboardButton(
                        f"❌ Reject #{i+1}", 
                        callback_data=f"reject_wd_{wd['user_id']}_{wd['requested_at']}"
                    )
                )
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            
            bot.edit_message_text(
                wd_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
    
    elif action == 'screenshots':
        # View pending screenshots
        pending_submissions = get_pending_submissions()
        
        if not pending_submissions:
            bot.edit_message_text(
                "📸 Screenshot Verification\n\n✅ No pending submissions",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            sub_text = f"📸 Pending Screenshots ({len(pending_submissions)}):\n\n"
            for i, sub in enumerate(pending_submissions[:5], 1):
                try:
                    user = get_user_data(sub['user_id'])
                    user_name = user['first_name'] if user else 'Unknown'
                    tasks = get_tasks()
                    task = next((t for t in tasks if t['id'] == sub['task_id']), {'title': 'Unknown Task'})
                except:
                    user_name = 'Unknown'
                    task = {'title': 'Unknown Task'}
                
                sub_text += f"{i}. {user_name}\n"
                sub_text += f"📋 Task: {task['title']}\n"
                sub_text += f"📅 {sub['submitted_at']}\n\n"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📸 View Submissions", callback_data="admin_view_submissions"))
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            
            bot.edit_message_text(
                sub_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
    
    elif action == 'stats':
        # Show comprehensive statistics
        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
        except:
            users = {}
        
        try:
            with open(TASKS_FILE, 'r') as f:
                tasks = json.load(f)
        except:
            tasks = []
        
        try:
            with open(WITHDRAWALS_FILE, 'r') as f:
                withdrawals = json.load(f)
        except:
            withdrawals = []
        
        try:
            with open(SUBMISSIONS_FILE, 'r') as f:
                submissions = json.load(f)
        except:
            submissions = {}
        
        total_users = len(users)
        total_tasks = len(tasks)
        active_tasks = len([t for t in tasks if t.get('active', True)])
        pending_withdrawals = len([w for w in withdrawals if w['status'] == 'pending'])
        approved_withdrawals = len([w for w in withdrawals if w['status'] == 'approved'])
        total_balance = sum(user.get('balance', 0) for user in users.values())
        total_referrals = sum(user.get('referrals', 0) for user in users.values())
        
        # Count completed tasks
        completed_tasks = 0
        for user_subs in submissions.values():
            completed_tasks += len([s for s in user_subs if s['status'] == 'approved'])
        
        stats_text = (
            f"📊 Bot Statistics\n\n"
            f"👥 Total Users: {total_users}\n"
            f"📋 Total Tasks: {total_tasks}\n"
            f"✅ Active Tasks: {active_tasks}\n"
            f"🎯 Completed Tasks: {completed_tasks}\n"
            f"💰 Total Balance: ₹{total_balance}\n"
            f"🔗 Total Referrals: {total_referrals}\n"
            f"💸 Pending Withdrawals: {pending_withdrawals}\n"
            f"✅ Approved Withdrawals: {approved_withdrawals}\n\n"
            f"📈 Revenue: ₹{completed_tasks * 3} (avg)\n"
            f"📊 User Growth: {total_users} users"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif action == 'broadcast':
        # Broadcast message
        msg = bot.send_message(
            call.from_user.id,
            "📢 Enter broadcast message:"
        )
        bot.register_next_step_handler(msg, process_broadcast_message)
        bot.answer_callback_query(call.id)
        return
    
    elif action == 'settings':
        # Bot settings
        settings_text = (
            f"⚙️ Bot Settings\n\n"
            f"💰 Minimum Withdrawal: ₹{MIN_WITHDRAWAL}\n"
            f"🔗 Referral Reward: ₹{REWARD_PER_REFERRAL}\n"
            f"📋 Max Tasks per User: {MAX_TASKS_PER_USER}\n"
            f"📅 Daily Task Limit: {DAILY_TASK_LIMIT}\n\n"
            f"🏆 Milestone Bonuses:\n"
        )
        for milestone, bonus in MILESTONE_BONUSES.items():
            settings_text += f"• {milestone} referrals = ₹{bonus}\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(
            settings_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif action == 'logs':
        # Show activity logs
        try:
            with open(LOG_FILE, 'r') as f:
                logs = f.read().split('\n')[-10:]  # Last 10 entries
        except:
            logs = ["No logs available"]
        
        log_text = "📝 Activity Logs (Last 10):\n\n"
        for log in logs:
            if log.strip():
                log_text += f"• {log}\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(
            log_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif action == 'back':
        # Back to main admin panel
        handle_admin_panel_callback(call)
    
    bot.answer_callback_query(call.id)

# Additional Admin Callbacks for Task Management
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_add_task'))
def handle_add_task_callback(call):
    if not is_admin(call.from_user.id):
        return
    
    msg = bot.send_message(
        call.from_user.id,
        "📝 Add New Task\n\nPlease enter task details in this format:\n\n"
        "Title|Description|Link|Reward|Task Type\n\n"
        "Task Types: youtube_subscribe, instagram_follow, telegram_join, facebook_like, whatsapp_join\n\n"
        "Example:\n"
        "Subscribe to Channel|Subscribe to our YouTube channel|https://youtube.com/channel|5|youtube_subscribe"
    )
    bot.register_next_step_handler(msg, process_new_task)
    bot.answer_callback_query(call.id)

def process_new_task(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split('|')
        if len(parts) != 5:
            bot.reply_to(message, "❌ Invalid format. Please use: Title|Description|Link|Reward|Task Type")
            return
        
        title, description, link, reward, task_type = parts
        reward = int(reward)
        
        if task_type not in TASK_TYPES:
            bot.reply_to(message, f"❌ Invalid task type. Use: {', '.join(TASK_TYPES.keys())}")
            return
        
        # Generate task ID
        tasks = get_tasks()
        task_id = f"task_{len(tasks) + 1}_{int(time.time())}"
        
        new_task = {
            'id': task_id,
            'title': title.strip(),
            'description': description.strip(),
            'link': link.strip(),
            'reward': reward,
            'type': task_type,
            'active': True,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'completed_count': 0
        }
        
        # Add task to file
        tasks.append(new_task)
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
        
        task_type_hindi = TASK_TYPES[task_type]
        
        bot.reply_to(
            message,
            f"✅ Task added successfully!\n\n"
            f"📋 Title: {title}\n"
            f"🎯 Type: {task_type_hindi}\n"
            f"💰 Reward: ₹{reward}\n"
            f"🆔 Task ID: {task_id}"
        )
        
        log_activity(f"Admin {message.from_user.id} added new task: {title}")
        
    except ValueError:
        bot.reply_to(message, "❌ Reward must be a number")
    except Exception as e:
        bot.reply_to(message, f"❌ Error adding task: {str(e)}")

# Withdrawal approval handlers
@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_wd_'))
def handle_withdrawal_approval(call):
    if not is_admin(call.from_user.id):
        return
    
    try:
        _, _, user_id, requested_at = call.data.split('_', 3)
        
        # Update withdrawal status
        with open(WITHDRAWALS_FILE, 'r+') as f:
            withdrawals = json.load(f)
            for wd in withdrawals:
                if wd['user_id'] == user_id and wd['requested_at'] == requested_at:
                    wd['status'] = 'approved'
                    wd['approved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    wd['approved_by'] = call.from_user.id
                    break
            
            f.seek(0)
            json.dump(withdrawals, f, indent=2)
            f.truncate()
        
        # Notify user
        try:
            user = get_user_data(user_id)
            bot.send_message(
                user_id,
                f"✅ आपका निकासी अनुरोध स्वीकृत हो गया!\n\n"
                f"💰 राशि: ₹{wd['amount']}\n"
                f"💳 UPI ID: {wd.get('upi_id', 'N/A')}\n\n"
                "पेमेंट 24 घंटे के अंदर आपके अकाउंट में ट्रांसफर हो जाएगा।"
            )
        except:
            pass
        
        bot.answer_callback_query(call.id, "✅ Withdrawal approved!")
        log_activity(f"Admin {call.from_user.id} approved withdrawal for user {user_id}")
        
        # Refresh the withdrawal list
        bot.edit_message_text(
            f"✅ Withdrawal approved for user {user_id}",
            call.message.chat.id,
            call.message.message_id
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_wd_'))
def handle_withdrawal_rejection(call):
    if not is_admin(call.from_user.id):
        return
    
    try:
        _, _, user_id, requested_at = call.data.split('_', 3)
        
        msg = bot.send_message(
            call.from_user.id,
            "📝 Enter rejection reason:"
        )
        bot.register_next_step_handler(
            msg, 
            lambda m: process_withdrawal_rejection(m, user_id, requested_at)
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

def process_withdrawal_rejection(message, user_id, requested_at):
    if not is_admin(message.from_user.id):
        return
    
    reason = message.text
    
    # Update withdrawal status and restore user balance
    with open(WITHDRAWALS_FILE, 'r+') as f:
        withdrawals = json.load(f)
        for wd in withdrawals:
            if wd['user_id'] == user_id and wd['requested_at'] == requested_at:
                wd['status'] = 'rejected'
                wd['rejected_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                wd['rejected_by'] = message.from_user.id
                wd['rejection_reason'] = reason
                
                # Restore user balance
                user = get_user_data(user_id)
                if user:
                    update_user_data(user_id, field='balance', value=user['balance'] + wd['amount'])
                
                break
        
        f.seek(0)
        json.dump(withdrawals, f, indent=2)
        f.truncate()
    
    # Notify user
    try:
        bot.send_message(
            user_id,
            f"❌ आपका निकासी अनुरोध रद्द कर दिया गया।\n\n"
            f"📝 कारण: {reason}\n\n"
            f"💰 राशि ₹{wd['amount']} आपके बैलेंस में वापस कर दी गई है।"
        )
    except:
        pass
    
    bot.reply_to(
        message,
        f"✅ Withdrawal rejected for user {user_id}. Balance restored."
    )
    log_activity(f"Admin {message.from_user.id} rejected withdrawal for user {user_id}: {reason}")

def handle_admin_panel_callback(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Manage Tasks", callback_data="admin_tasks"),
        types.InlineKeyboardButton("👥 View Users", callback_data="admin_users")
    )
    markup.add(
        types.InlineKeyboardButton("💳 Withdrawals", callback_data="admin_withdrawals"),
        types.InlineKeyboardButton("📸 Screenshots", callback_data="admin_screenshots")
    )
    markup.add(
        types.InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    )
    markup.add(
        types.InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings"),
        types.InlineKeyboardButton("📝 Logs", callback_data="admin_logs")
    )
    
    bot.edit_message_text(
        "🔧 Admin Panel\n\nSelect an option:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('task_'))
def handle_task_selection(call):
    user_id = call.from_user.id
    if is_user_blocked(user_id):
        return
    
    task_id = call.data.split('_')[1]
    tasks = get_tasks()
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if not task:
        bot.answer_callback_query(call.id, "❌ कार्य अब उपलब्ध नहीं है")
        return
    
    task_type_hindi = TASK_TYPES.get(task.get('type', 'general'), 'सामान्य कार्य')
    
    task_msg = (
        f"🎯 कार्य: {task['title']}\n"
        f"📱 प्रकार: {task_type_hindi}\n"
        f"💰 रिवॉर्ड: ₹{task['reward']}\n\n"
        f"📝 विवरण:\n{task['description']}\n\n"
        f"🔗 लिंक: {task.get('link', 'N/A')}\n\n"
        f"📋 निर्देश:\n"
        f"1. ऊपर दिए गए लिंक पर जाएं\n"
        f"2. कार्य पूरा करें ({task_type_hindi})\n"
        f"3. कार्य पूरा होने का स्क्रीनशॉट लें\n"
        f"4. स्क्रीनशॉट को इस चैट में भेजें\n\n"
        f"⚠️ कार्य पूरा करने के बाद, स्क्रीनशॉट को फोटो के रूप में इस चैट में भेजें।"
    )
    
    # Add task completion button
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "✅ कार्य पूरा करके स्क्रीनशॉट भेजें", 
        callback_data=f"complete_{task_id}"
    ))
    
    bot.send_message(
        call.message.chat.id,
        task_msg,
        reply_markup=markup,
        disable_web_page_preview=False
    )
    bot.answer_callback_query(call.id)

# Add global variable to track current task submissions
user_current_task = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith('complete_'))
def handle_complete_task(call):
    user_id = call.from_user.id
    if is_user_blocked(user_id):
        return
    
    task_id = call.data.split('_')[1]
    user_current_task[user_id] = task_id
    
    bot.send_message(
        call.message.chat.id,
        "📸 कृपया कार्य पूरा होने का स्क्रीनशॉट भेजें:\n\n"
        "⚠️ सुनिश्चित करें कि स्क्रीनशॉट में:\n"
        "• आपका यूजरनेम दिखाई दे\n"
        "• कार्य पूरा होने का प्रमाण हो\n"
        "• इमेज स्पष्ट और पूरी दिखाई दे\n\n"
        "अब स्क्रीनशॉट को फोटो के रूप में भेजें।"
    )
    bot.answer_callback_query(call.id, "📸 अब स्क्रीनशॉट भेजें")

@bot.message_handler(content_types=['photo'])
def handle_proof_submission(message):
    user_id = message.from_user.id
    if is_user_blocked(user_id):
        return
    
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ पहले /start कमांड के साथ बॉट शुरू करें")
        return
    
    # Get the task ID for this user
    task_id = user_current_task.get(user_id, "general_task")
    
    file_id = message.photo[-1].file_id
    record_submission(user_id, task_id, file_id)
    
    # Clear the current task
    if user_id in user_current_task:
        del user_current_task[user_id]
    
    bot.reply_to(
        message,
        "✅ प्रमाण सफलतापूर्वक सबमिट हो गया!\n\n"
        "आपका सबमिशन समीक्षा के लिए भेजा गया है। स्वीकृति के बाद आपको सूचित किया जाएगा।\n"
        "💰 स्वीकृति के बाद रिवॉर्ड आपके बैलेंस में जोड़ दिया जाएगा।"
    )
    log_activity(f"User {user_id} submitted proof for task {task_id}")

# ======================
# Admin Handlers
# ======================

@bot.message_handler(commands=['newtask'])
def handle_new_task(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only command")
        return
    
    msg = bot.reply_to(message, "📝 Enter task title:")
    bot.register_next_step_handler(msg, process_task_title)

def process_task_title(message):
    title = message.text
    msg = bot.reply_to(message, "📝 Enter task description:")
    bot.register_next_step_handler(msg, lambda m: process_task_description(m, title))

def process_task_description(message, title):
    description = message.text
    msg = bot.reply_to(message, "💰 Enter task reward amount:")
    bot.register_next_step_handler(msg, lambda m: process_task_reward(m, title, description))

def process_task_reward(message, title, description):
    try:
        reward = float(message.text)
        task_id = f"task_{int(datetime.now().timestamp())}"
        
        new_task = {
            "id": task_id,
            "title": title,
            "description": description,
            "reward": reward,
            "active": True,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        add_task(new_task)
        bot.reply_to(
            message,
            f"✅ New task created!\n\n"
            f"📌 {title}\n"
            f"💰 ₹{reward}\n"
            f"🆔 {task_id}"
        )
        log_activity(f"Admin {message.from_user.id} created new task: {task_id}")
    except ValueError:
        bot.reply_to(message, "❌ Invalid reward amount. Please enter a number.")

@bot.message_handler(commands=['approve'])
def handle_approve(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only command")
        return
    
    pending = get_pending_submissions()
    if not pending:
        bot.reply_to(message, "✅ No pending submissions")
        return
    
    markup = types.InlineKeyboardMarkup()
    for sub in pending[:10]:
        user = get_user_data(sub['user_id'])
        task = next((t for t in get_tasks() if t['id'] == sub['task_id']), None)
        task_title = task['title'] if task else "Unknown Task"
        
        markup.add(types.InlineKeyboardButton(
            text=f"User {user['first_name']} - {task_title}",
            callback_data=f"review_{sub['user_id']}_{sub['task_id']}_{sub['file_id']}"
        ))
    
    bot.reply_to(
        message,
        "📝 Pending Submissions\n\n"
        "Click to review each submission:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('review_'))
def handle_submission_review(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Admin only")
        return
    
    _, user_id, task_id, file_id = call.data.split('_')
    user = get_user_data(user_id)
    task = next((t for t in get_tasks() if t['id'] == task_id), None)
    
    if not task:
        bot.answer_callback_query(call.id, "❌ Task not found")
        return
    
    bot.send_photo(
        call.from_user.id,
        file_id,
        caption=f"📌 Task: {task['title']}\n"
               f"💰 Reward: ₹{task['reward']}\n"
               f"👤 User: {user['first_name']} (ID: {user_id})"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{task_id}_{file_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{task_id}_{file_id}")
    )
    
    bot.send_message(
        call.from_user.id,
        "Approve or reject this submission?",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_approval_decision(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Admin only")
        return
    
    action, user_id, task_id, file_id = call.data.split('_')
    task = next((t for t in get_tasks() if t['id'] == task_id), None)
    
    if action == 'approve':
        user = get_user_data(user_id)
        new_balance = user['balance'] + task['reward']
        update_user_data(user_id, field='balance', value=new_balance)
        
        # Add to completed tasks
        completed_tasks = user.get('completed_tasks', [])
        completed_tasks.append({
            'task_id': task_id,
            'title': task['title'],
            'reward': task['reward'],
            'completed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        update_user_data(user_id, field='completed_tasks', value=completed_tasks)
        
        # Update task completion count
        tasks = get_tasks()
        for i, t in enumerate(tasks):
            if t['id'] == task_id:
                tasks[i]['completed_count'] = tasks[i].get('completed_count', 0) + 1
                break
        
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
        
        update_submission_status(user_id, task_id, 'approved')
        
        bot.send_message(
            user_id,
            f"🎉 आपका '{task['title']}' कार्य स्वीकृत हो गया!\n"
            f"💰 ₹{task['reward']} आपके बैलेंस में जोड़ दिए गए।\n"
            f"💵 नया बैलेंस: ₹{new_balance}\n\n"
            f"✅ बधाई हो! आप और भी कार्य पूरे कर सकते हैं।"
        )
        
        bot.answer_callback_query(call.id, "✅ Submission approved")
        log_activity(f"Admin {call.from_user.id} approved submission from {user_id} for task {task_id}")
    else:
        msg = bot.send_message(
            call.from_user.id,
            "📝 Please enter rejection reason:"
        )
        bot.register_next_step_handler(
            msg, 
            lambda m: process_rejection_reason(m, user_id, task_id, file_id)
        )
        bot.answer_callback_query(call.id)

def process_rejection_reason(message, user_id, task_id, file_id):
    if not is_admin(message.from_user.id):
        return
        
    reason = message.text
    task = next((t for t in get_tasks() if t['id'] == task_id), None)
    
    update_submission_status(user_id, task_id, 'rejected', reason)
    
    bot.send_message(
        user_id,
        f"❌ आपका '{task['title']}' कार्य रद्द कर दिया गया।\n\n"
        f"📝 कारण: {reason}\n\n"
        f"🔄 आप सही प्रमाण के साथ दोबारा कोशिश कर सकते हैं।\n"
        f"💡 सुझाव: स्क्रीनशॉट में आपका यूजरनेम और कार्य पूरा होने का स्पष्ट प्रमाण होना चाहिए।"
    )
    
    bot.reply_to(
        message,
        "✅ User has been notified about the rejection."
    )
    log_activity(f"Admin {message.from_user.id} rejected submission from {user_id} for task {task_id}")

@bot.message_handler(commands=['users'])
def handle_users_list(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only command")
        return
    
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    response = "👥 Users List\n\n"
    for uid, data in users.items():
        response += (
            f"👤 {data.get('first_name', 'Unknown')} (ID: {uid})\n"
            f"💰 Balance: ₹{data.get('balance', 0)}\n"
            f"👥 Referrals: {data.get('referrals', 0)}\n"
            f"📅 Joined: {data.get('joined', 'N/A')}\n"
            f"🚫 Blocked: {'Yes' if data.get('blocked', False) else 'No'}\n\n"
        )
    
    for i in range(0, len(response), 4096):
        bot.reply_to(message, response[i:i+4096])

@bot.message_handler(commands=['block'])
def handle_block_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only command")
        return
    
    try:
        target_id = message.text.split()[1]
        update_user_data(target_id, 'blocked', True)
        block_user(target_id)
        bot.reply_to(message, f"✅ User {target_id} has been blocked")
        log_activity(f"Admin {message.from_user.id} blocked user {target_id}")
    except (IndexError, KeyError):
        bot.reply_to(message, "❌ Usage: /block <user_id>")

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only command")
        return
    
    try:
        text = message.text.split(' ', 1)[1]
    except IndexError:
        bot.reply_to(message, "❌ Usage: /broadcast <message>")
        return
    
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    success = 0
    failed = 0
    for uid in users.keys():
        try:
            bot.send_message(uid, f"📢 Admin Announcement:\n\n{text}")
            success += 1
        except Exception as e:
            failed += 1
    
    bot.reply_to(
        message,
        f"📢 Broadcast completed!\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}"
    )
    log_activity(f"Admin {message.from_user.id} sent broadcast to {success} users")

@bot.message_handler(commands=['admin'])
def handle_admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only command")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
        types.InlineKeyboardButton("👥 Users", callback_data="admin_users")
    )
    markup.row(
        types.InlineKeyboardButton("📝 Pending Tasks", callback_data="admin_pending"),
        types.InlineKeyboardButton("💸 Withdrawals", callback_data="admin_withdrawals")
    )
    markup.row(
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("➕ New Task", callback_data="admin_newtask")
    )
    
    bot.reply_to(
        message,
        "🔧 Admin Panel\n\nSelect an option:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Admin only")
        return
    
    action = call.data.split('_')[1]
    
    if action == 'stats':
        # Get statistics
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        
        total_users = len(users)
        total_balance = sum(user.get('balance', 0) for user in users.values())
        total_referrals = sum(user.get('referrals', 0) for user in users.values())
        
        stats_text = (
            f"📊 Bot Statistics\n\n"
            f"👥 Total Users: {total_users}\n"
            f"💰 Total Balance: ₹{total_balance}\n"
            f"👥 Total Referrals: {total_referrals}\n"
            f"📅 Active Today: {len([u for u in users.values() if u.get('joined', '').startswith(datetime.now().strftime('%Y-%m-%d'))])}"
        )
        
        bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id
        )
    
    elif action == 'users':
        # Show users list
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        
        users_text = "👥 Recent Users:\n\n"
        for i, (uid, data) in enumerate(list(users.items())[-10:]):
            users_text += f"{i+1}. {data.get('first_name', 'Unknown')} (ID: {uid})\n"
            users_text += f"   💰 ₹{data.get('balance', 0)} | 👥 {data.get('referrals', 0)} refs\n\n"
        
        bot.edit_message_text(
            users_text,
            call.message.chat.id,
            call.message.message_id
        )
    
    elif action == 'pending':
        # Show pending submissions
        pending = get_pending_submissions()
        if not pending:
            bot.edit_message_text(
                "✅ No pending submissions",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            pending_text = f"📝 Pending Submissions ({len(pending)}):\n\n"
            for sub in pending[:5]:
                user = get_user_data(sub['user_id'])
                pending_text += f"👤 {user['first_name']} - {sub['task_id']}\n"
                pending_text += f"📅 {sub['submitted_at']}\n\n"
            
            bot.edit_message_text(
                pending_text,
                call.message.chat.id,
                call.message.message_id
            )
    
    elif action == 'withdrawals':
        # Show pending withdrawals
        withdrawals = get_pending_withdrawals()
        if not withdrawals:
            bot.edit_message_text(
                "✅ No pending withdrawals",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            wd_text = f"💸 Pending Withdrawals ({len(withdrawals)}):\n\n"
            for wd in withdrawals[:5]:
                user = get_user_data(wd['user_id'])
                wd_text += f"👤 {user['first_name']} - ₹{wd['amount']} via {wd.get('upi_id', wd.get('method', 'UPI'))}\n"
                wd_text += f"📅 {wd['requested_at']}\n\n"
            
            bot.edit_message_text(
                wd_text,
                call.message.chat.id,
                call.message.message_id
            )
    
    elif action == 'broadcast':
        msg = bot.send_message(
            call.from_user.id,
            "📢 Enter broadcast message:"
        )
        bot.register_next_step_handler(msg, process_broadcast_message)
    
    elif action == 'newtask':
        msg = bot.send_message(
            call.from_user.id,
            "📝 Enter task title:"
        )
        bot.register_next_step_handler(msg, process_task_title)
    
    bot.answer_callback_query(call.id)

def process_broadcast_message(message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    success = 0
    failed = 0
    for uid in users.keys():
        try:
            bot.send_message(uid, f"📢 Admin Announcement:\n\n{text}")
            success += 1
        except Exception as e:
            failed += 1
    
    bot.reply_to(
        message,
        f"📢 Broadcast completed!\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}"
    )
    log_activity(f"Admin {message.from_user.id} sent broadcast to {success} users")

# ======================
# Sample Data Creation
# ======================

def create_sample_tasks():
    """Create sample tasks for testing if no tasks exist"""
    tasks = get_tasks()
    if len(tasks) == 0:
        sample_tasks = [
            {
                'id': f"task_sample_1_{int(time.time())}",
                'title': 'YouTube Channel Subscribe करें',
                'description': 'हमारे YouTube चैनल को सब्सक्राइब करें और बेल आइकन दबाएं',
                'link': 'https://youtube.com/@example',
                'reward': 5,
                'type': 'youtube_subscribe',
                'active': True,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'completed_count': 0
            },
            {
                'id': f"task_sample_2_{int(time.time())}",
                'title': 'Instagram Page Follow करें',
                'description': 'हमारे Instagram पेज को फॉलो करें',
                'link': 'https://instagram.com/example',
                'reward': 3,
                'type': 'instagram_follow',
                'active': True,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'completed_count': 0
            },
            {
                'id': f"task_sample_3_{int(time.time())}",
                'title': 'Telegram Group Join करें',
                'description': 'हमारे Telegram ग्रुप में शामिल हों',
                'link': 'https://t.me/example',
                'reward': 4,
                'type': 'telegram_join',
                'active': True,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'completed_count': 0
            },
            {
                'id': f"task_sample_4_{int(time.time())}",
                'title': 'Facebook Page Like करें',
                'description': 'हमारे Facebook पेज को लाइक करें',
                'link': 'https://facebook.com/example',
                'reward': 3,
                'type': 'facebook_like',
                'active': True,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'completed_count': 0
            },
            {
                'id': f"task_sample_5_{int(time.time())}",
                'title': 'WhatsApp Group Join करें',
                'description': 'हमारे WhatsApp ग्रुप में शामिल हों',
                'link': 'https://chat.whatsapp.com/example',
                'reward': 2,
                'type': 'whatsapp_join',
                'active': True,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'completed_count': 0
            }
        ]
        
        with open(TASKS_FILE, 'w') as f:
            json.dump(sample_tasks, f, indent=2)
        
        log_activity("Sample tasks created successfully")
        print("✅ Sample tasks created successfully")

# ======================
# Main Function
# ======================

def main():
    # Initialize data files
    initialize_data_files()
    
    # Create sample tasks if none exist
    create_sample_tasks()
    
    # Start keep alive server
    keep_alive()
    
    # Start background threads
    threading.Thread(target=self_ping_loop, daemon=True).start()
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    
    # Start bot
    log_activity("Bot started successfully")
    bot.infinity_polling()

if __name__ == "__main__":
    main()