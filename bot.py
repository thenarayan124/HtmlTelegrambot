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
ADMIN_ID = os.getenv('ADMIN_ID', '5367009004')
MIN_WITHDRAWAL = 100
REWARD_PER_REFERRAL = 10
MAX_TASKS_PER_USER = 3
DAILY_TASK_LIMIT = 5

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
    return str(user_id) == ADMIN_ID

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
                        data['referrals'] += 1
                        data['balance'] += REWARD_PER_REFERRAL
                        f.seek(0)
                        json.dump(users, f)
                        f.truncate()
                        log_activity(f"User {user_id} joined via referral from {uid}")
                        break
        
        update_user_data(user_id, new_user)
        log_activity(f"New user registered: {user_id}")
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('📋 Available Tasks'))
    markup.add(types.KeyboardButton('💰 Balance'), types.KeyboardButton('👥 Refer Friends'))
    markup.add(types.KeyboardButton('💸 Withdraw'), types.KeyboardButton('📊 My Tasks'))
    markup.add(types.KeyboardButton('❓ Help'), types.KeyboardButton('📞 Support'))
    
    bot.send_message(
        chat_id,
        f"👋 Welcome {first_name} to TaskRewardBot!\n\n"
        "✅ Earn money by completing simple tasks\n"
        "📸 Submit proof to get rewards\n"
        "👥 Refer friends for bonus cash\n"
        "💸 Withdraw your earnings anytime",
        reply_markup=markup
    )

@bot.message_handler(commands=['balance'])
def handle_balance(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ You need to start the bot first with /start")
        return
    
    bot.reply_to(
        message,
        f"💰 Your current balance: ${user['balance']}\n\n"
        f"👥 Referrals: {user['referrals']} (${user['referrals'] * REWARD_PER_REFERRAL})\n"
        f"💵 Minimum withdrawal: ${MIN_WITHDRAWAL}"
    )

@bot.message_handler(commands=['refer'])
def handle_refer(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ You need to start the bot first with /start")
        return
    
    bot.reply_to(
        message,
        f"👥 Refer your friends and earn ${REWARD_PER_REFERRAL} for each!\n\n"
        f"Your referral link:\n"
        f"https://t.me/YourBotUsername?start={user['referral_code']}\n\n"
        f"Total referrals: {user['referrals']}\n"
        f"Earned from referrals: ${user['referrals'] * REWARD_PER_REFERRAL}"
    )

@bot.message_handler(commands=['withdrawal'])
def handle_withdrawal(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ You need to start the bot first with /start")
        return
    
    if user['balance'] < MIN_WITHDRAWAL:
        bot.reply_to(
            message,
            f"❌ Minimum withdrawal amount is ${MIN_WITHDRAWAL}\n"
            f"Your current balance: ${user['balance']}"
        )
        return
    
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('PayPal', 'Bank Transfer', 'Cancel')
    
    msg = bot.reply_to(
        message,
        "💸 Select your withdrawal method:",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_withdrawal_method)

def process_withdrawal_method(message):
    user_id = message.from_user.id
    if is_user_blocked(user_id):
        return
    
    method = message.text
    
    if method.lower() == 'cancel':
        bot.reply_to(message, "❌ Withdrawal canceled", reply_markup=types.ReplyKeyboardRemove())
        return
    
    user = get_user_data(user_id)
    request_withdrawal(user_id, user['balance'], method)
    
    bot.reply_to(
        message,
        f"✅ Withdrawal request submitted for ${user['balance']} via {method}\n\n"
        "Admin will process your request within 24 hours.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    log_activity(f"User {user_id} requested ${user['balance']} withdrawal via {method}")

@bot.message_handler(commands=['help'])
def handle_help(message):
    if is_user_blocked(message.from_user.id):
        return
    
    help_text = (
        "📚 TaskRewardBot Help\n\n"
        "/start - Start the bot and register\n"
        "/balance - Check your earnings\n"
        "/refer - Get your referral link\n"
        "/withdrawal - Request money withdrawal\n"
        "/help - Show this help message\n\n"
        "📌 How it works:\n"
        "1. Browse available tasks\n"
        "2. Complete a task\n"
        "3. Submit proof (screenshot)\n"
        "4. Get reward after approval\n"
        "5. Withdraw your earnings\n\n"
        "👥 Refer friends to earn extra money!"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: message.text == '📋 Available Tasks')
def show_available_tasks(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    tasks = get_tasks()
    
    if not tasks:
        bot.reply_to(message, "❌ No tasks available at the moment. Check back later!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for task in tasks:
        if task.get('active', True):
            markup.add(types.InlineKeyboardButton(
                text=f"{task['title']} (${task['reward']})",
                callback_data=f"task_{task['id']}"
            ))
    
    bot.reply_to(
        message,
        "📋 Available Tasks\n\n"
        "Click on a task to view details and complete it:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == '💰 Balance')
def handle_balance_button(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ You need to start the bot first with /start")
        return
    
    bot.reply_to(
        message,
        f"💰 Your current balance: ${user['balance']}\n\n"
        f"👥 Referrals: {user['referrals']} (${user['referrals'] * REWARD_PER_REFERRAL})\n"
        f"💵 Minimum withdrawal: ${MIN_WITHDRAWAL}"
    )

@bot.message_handler(func=lambda message: message.text == '👥 Refer Friends')
def handle_refer_button(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ You need to start the bot first with /start")
        return
    
    bot.reply_to(
        message,
        f"👥 Refer your friends and earn ${REWARD_PER_REFERRAL} for each!\n\n"
        f"Your referral link:\n"
        f"https://t.me/YourBotUsername?start={user['referral_code']}\n\n"
        f"Total referrals: {user['referrals']}\n"
        f"Earned from referrals: ${user['referrals'] * REWARD_PER_REFERRAL}"
    )

@bot.message_handler(func=lambda message: message.text == '💸 Withdraw')
def handle_withdraw_button(message):
    if is_user_blocked(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ You need to start the bot first with /start")
        return
    
    if user['balance'] < MIN_WITHDRAWAL:
        bot.reply_to(
            message,
            f"❌ Minimum withdrawal amount is ${MIN_WITHDRAWAL}\n"
            f"Your current balance: ${user['balance']}"
        )
        return
    
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('PayPal', 'Bank Transfer', 'Cancel')
    
    msg = bot.reply_to(
        message,
        "💸 Select your withdrawal method:",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_withdrawal_method)

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

@bot.message_handler(func=lambda message: message.text == '❓ Help')
def handle_help_button(message):
    if is_user_blocked(message.from_user.id):
        return
    
    help_text = (
        "📚 TaskRewardBot Help\n\n"
        "📋 Available Tasks - Browse and complete tasks\n"
        "💰 Balance - Check your earnings\n"
        "👥 Refer Friends - Get your referral link\n"
        "💸 Withdraw - Request money withdrawal\n"
        "📊 My Tasks - View your task history\n"
        "❓ Help - Show this help message\n"
        "📞 Support - Contact support\n\n"
        "📌 How it works:\n"
        "1. Browse available tasks\n"
        "2. Complete a task\n"
        "3. Submit proof (screenshot)\n"
        "4. Get reward after approval\n"
        "5. Withdraw your earnings\n\n"
        "👥 Refer friends to earn extra money!"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: message.text == '📞 Support')
def handle_support_button(message):
    if is_user_blocked(message.from_user.id):
        return
    
    support_text = (
        "📞 Support\n\n"
        "If you need help, contact our support team:\n\n"
        "👤 Admin: @YourAdminUsername\n"
        "📧 Email: support@taskrewardbot.com\n"
        "🌐 Website: https://taskrewardbot.com\n\n"
        "⏰ Response time: Within 24 hours\n\n"
        "Common issues:\n"
        "• Task not approved - Check requirements\n"
        "• Withdrawal pending - Wait 24 hours\n"
        "• Bot not responding - Try /start"
    )
    bot.reply_to(message, support_text)

@bot.callback_query_handler(func=lambda call: call.data.startswith('task_'))
def handle_task_selection(call):
    user_id = call.from_user.id
    if is_user_blocked(user_id):
        return
    
    task_id = call.data.split('_')[1]
    tasks = get_tasks()
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if not task:
        bot.answer_callback_query(call.id, "❌ Task no longer available")
        return
    
    bot.send_message(
        call.message.chat.id,
        f"📌 Task: {task['title']}\n"
        f"💰 Reward: ${task['reward']}\n\n"
        f"📝 Description:\n{task['description']}\n\n"
        "⚠️ After completing the task, send the screenshot as a photo to this chat."
    )
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_proof_submission(message):
    user_id = message.from_user.id
    if is_user_blocked(user_id):
        return
    
    user = get_user_data(user_id)
    
    if not user:
        bot.reply_to(message, "❌ You need to start the bot first with /start")
        return
    
    file_id = message.photo[-1].file_id
    record_submission(user_id, "temp_task_id", file_id)
    
    bot.reply_to(
        message,
        "✅ Proof submitted successfully!\n\n"
        "Your submission is under review. You'll be notified when it's approved."
    )
    log_activity(f"User {user_id} submitted proof for task")

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
            f"💰 ${reward}\n"
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
               f"💰 Reward: ${task['reward']}\n"
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
        update_user_data(user_id, 'balance', new_balance)
        
        update_submission_status(user_id, task_id, 'approved')
        
        bot.send_message(
            user_id,
            f"🎉 Your submission for '{task['title']}' has been approved!\n"
            f"💰 ${task['reward']} has been added to your balance.\n"
            f"💵 New balance: ${new_balance}"
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
    reason = message.text
    task = next((t for t in get_tasks() if t['id'] == task_id), None)
    
    update_submission_status(user_id, task_id, 'rejected', reason)
    
    bot.send_message(
        user_id,
        f"❌ Your submission for '{task['title']}' was rejected.\n\n"
        f"📝 Reason: {reason}\n\n"
        "You can try again with a different proof."
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
            f"💰 Balance: ${data.get('balance', 0)}\n"
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
            f"💰 Total Balance: ${total_balance}\n"
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
            users_text += f"   💰 ${data.get('balance', 0)} | 👥 {data.get('referrals', 0)} refs\n\n"
        
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
                wd_text += f"👤 {user['first_name']} - ${wd['amount']} via {wd['method']}\n"
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
# Main Function
# ======================

def main():
    # Initialize data files
    initialize_data_files()
    
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