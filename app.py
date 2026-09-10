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
    # Regex: số đánh 2 chữ số, khoảng trắng tùy ý, từ khóa, khoảng trắng tùy ý, số tiền, đơn vị
    pattern = r'(\d{2})(\s*)([a-zA-Z_đ]+)(\s*)(\d+)([kn]?)'
    
    def replace_match(m):
        so_danh = m.group(1)
        space1 = m.group(2)
        keyword = m.group(3)
        space2 = m.group(4)
        so_tien = m.group(5)
        unit = m.group(6) or 'n'
        
        if keyword in EXCLUDED:
            return m.group(0)
        if keyword not in KEYWORDS:
            return m.group(0)
        
        new_tien = tinh_tien(so_tien)
        if new_tien is None:
            return m.group(0)
        
        return so_danh + space1 + keyword + space2 + new_tien + unit
    
    return re.sub(pattern, replace_match, text)

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
