import os
import re
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask

KEYWORDS = ['b', 'd', 'dd', 'bao', 'bl', 'lô', 'lo', '₫', 'đ', 'dđ', 'đđ', 'dauduoi', 'dau', 'dui', 'duoi', 'đầu', 'đuôi']
EXCLUDED = ['dx', 'dt', 'da', 'xc', 'xdao']

def tinh_tien(so_tien):
    try:
        amount = float(so_tien.replace(',', '.'))
    except:
        return None
    if amount <= 0:
        return None
    new_amount = amount * 0.93
    rounded = round(new_amount * 10) / 10
    formatted = str(rounded)
    if formatted.endswith('.0'):
        formatted = formatted[:-2]
    return formatted

def process_text(text):
    tokens = re.split(r'(\s+)', text)
    output = []
    so_danh = None
    
    for token in tokens:
        if re.match(r'^\s+$', token):
            output.append(token)
            continue
        
        # Nếu token là số 2 chữ số
        if re.match(r'^\d{2}$', token):
            so_danh = token
            output.append(token)
            continue
        
        # Nếu token là số 3 chữ số trở lên
        if re.match(r'^\d{3,}$', token):
            so_danh = None
            output.append(token)
            continue
        
        # Nếu token là từ khóa + số tiền (b50n, dd100n)
        match = re.match(r'^([a-zA-Z_đ]+)(\d+)([kn]?)$', token)
        if match:
            keyword = match.group(1)
            so_tien = match.group(2)
            unit = match.group(3) or 'n'
            if so_danh and keyword not in EXCLUDED and keyword in KEYWORDS:
                new_tien = tinh_tien(so_tien)
                if new_tien:
                    output.append(keyword + new_tien + unit)
                    continue
            output.append(token)
            continue
        
        output.append(token)
    
    return ''.join(output)

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

@app_flask.route('/health')
def health():
    return "OK"

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Thiếu TELEGRAM_TOKEN!")

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    await update.message.reply_text("Gửi văn bản số đề, bot xử lý theo luật 0.93.")

async def handle(update: Update, context):
    result = process_text(update.message.text)
    await update.message.reply_text(result)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

def run_flask():
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    application.run_polling()
