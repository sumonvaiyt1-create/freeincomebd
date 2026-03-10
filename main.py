import telebot
from telebot import types
import random
import sqlite3
from flask import Flask
from threading import Thread

# Flask setup (বট চালু রাখার জন্য)
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# আপনার টোকেন এবং আইডি
API_TOKEN = '8742116689:AAGjIPzOvmJCg6ncYPutuxCOrZiKC40Ysbg'
OWNER_ID = 8005459073 
bot = telebot.TeleBot(API_TOKEN)

GROUP_LINK = "https://t.me/sumonvaiyt"
AD_LINKS = ["https://omg10.com/4/10614284", "https://omg10.com/4/10700578", "https://omg10.com/4/10700627", "https://omg10.com/4/10480367"]

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance REAL, referred_by INTEGER)''')
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

init_db()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    # রেফারেল চেক
    args = message.text.split()
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    new_user = cursor.fetchone()
    
    if new_user is None:
        ref_id = None
        if len(args) > 1 and args[1].isdigit():
            ref_id = int(args[1])
            if ref_id != user_id:
                update_balance(ref_id, 2.0) # রেফারের জন্য ২ টাকা
                bot.send_message(ref_id, "🔔 আপনার লিঙ্কে কেউ জয়েন করেছে! আপনি ২ টাকা বোনাস পেয়েছেন।")
        
        cursor.execute("INSERT INTO users (user_id, balance, referred_by) VALUES (?, 0, ?)", (user_id, ref_id))
        conn.commit()
    conn.close()

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('📺 বিজ্ঞাপন দেখুন', '💰 ব্যালেন্স', '👥 রেফার করুন', '💳 উত্তোলন', '📢 গ্রুপ লিঙ্ক')
    bot.send_message(user_id, "স্বাগতম! Money Share বটে বিজ্ঞাপন দেখে আয় করুন।", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    if '📺 বিজ্ঞাপন দেখুন' in m.text:
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("বিজ্ঞাপন দেখুন 🔗", url=random.choice(AD_LINKS)))
        mk.add(types.InlineKeyboardButton("বোনাস নিন ✅", callback_data="bonus"))
        bot.send_message(m.chat.id, "বিজ্ঞাপনটি দেখে ২০ পয়সা বোনাস নিন।", reply_markup=mk)
    
    elif '💰 ব্যালেন্স' in m.text:
        bot.send_message(m.chat.id, f"আপনার বর্তমান ব্যালেন্স: ৳{get_user(m.chat.id):.2f}")
    
    elif '👥 রেফার করুন' in m.text:
        ref_link = f"https://t.me/{(bot.get_me()).username}?start={m.chat.id}"
        bot.send_message(m.chat.id, f"আপনার রেফারেল লিঙ্ক:\n{ref_link}\n\nপ্রতি সফল রেফারে পাবেন ২ টাকা!")

    elif '📢 গ্রুপ লিঙ্ক' in m.text:
        bot.send_message(m.chat.id, f"আমাদের অফিশিয়াল গ্রুপ: {GROUP_LINK}")

    elif '💳 উত্তোলন' in m.text:
        if get_user(m.chat.id) < 50: # মিনিমাম উইথড্র ৫০ টাকা সেট করলাম
            bot.send_message(m.chat.id, "মিনিমাম ৫০ টাকা হলে উইথড্র করতে পারবেন।")
        else:
            mk = types.InlineKeyboardMarkup()
            mk.add(types.InlineKeyboardButton("বিকাশ", callback_data="wit_bkash"),
                   types.InlineKeyboardButton("নগদ", callback_data="wit_nagad"))
            bot.send_message(m.chat.id, "পেমেন্ট মেথড সিলেক্ট করুন:", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith("wit_"))
def withdraw_method(call):
    method = "বিকাশ" if "bkash" in call.data else "নগদ"
    msg = bot.send_message(call.message.chat.id, f"আপনার {method} নম্বর এবং টাকার পরিমাণ লিখে পাঠান।")
    bot.register_next_step_handler(msg, process_withdrawal, method)

def process_withdrawal(m, method):
    admin_msg = f"🔔 **উইথড্র রিকোয়েস্ট!**\nID: `{m.chat.id}`\nমেথড: {method}\nতথ্য: {m.text}"
    bot.send_message(OWNER_ID, admin_msg, parse_mode="Markdown")
    bot.send_message(m.chat.id, "আপনার রিকোয়েস্ট সফলভাবে অ্যাডমিনের কাছে পাঠানো হয়েছে।")

@bot.callback_query_handler(func=lambda call: call.data == "bonus")
def earn_bonus(call):
    update_balance(call.message.chat.id, 0.20) # ২০ পয়সা
    bot.answer_callback_query(call.id, "৳০.২০ যোগ হয়েছে!")
    bot.edit_message_text(f"বোনাস সফল! বর্তমান ব্যালেন্স: ৳{get_user(call.message.chat.id):.2f}", call.message.chat.id, call.message.message_id)

def start_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    start_bot()
